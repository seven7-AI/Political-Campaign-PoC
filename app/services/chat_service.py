import os
from supabase import create_client, Client
from neo4j import GraphDatabase
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import SupabaseVectorStore
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import logging
from fastapi import WebSocket
from typing import List, Dict
from .email_service import EmailService
import json

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("chat_service.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        load_dotenv()
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        neo4j_uri = os.getenv("NEO4J_URI")
        neo4j_user = os.getenv("NEO4J_USER")
        neo4j_password = os.getenv("NEO4J_PASSWORD")
        
        if not all([supabase_url, supabase_key, neo4j_uri, neo4j_user, neo4j_password]):
            logger.error("Missing configuration for Supabase or Neo4j")
            raise ValueError("Configuration missing")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized")
        
        self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        logger.info("Neo4j driver initialized")
        
        self.embeddings = OpenAIEmbeddings(model="text-embedding-ada-002", openai_api_key=os.getenv("OPENAI_API_KEY"))
        self.vector_store = SupabaseVectorStore(
            client=self.supabase,
            embedding=self.embeddings,
            table_name="document_embeddings",
            query_name="match_documents"
        )
        self.llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=os.getenv("OPENAI_API_KEY"))
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(search_kwargs={"k": 3})
        )
        self.email_service = EmailService()
        logger.info("LangChain QA chain and email service initialized")

    def close(self):
        self.neo4j_driver.close()
        logger.info("Neo4j driver closed")

    def get_user_documents(self, user_id: str) -> List[Dict]:
        try:
            with self.neo4j_driver.session() as session:
                result = session.run("""
                    MATCH (u:User {user_id: $user_id})-[:PARTICIPATES_IN]->(c:Campaign)-[:CONTAINS_DOCUMENT]->(d:Document)
                    RETURN d.document_id AS document_id, d.file_name AS file_name
                """, user_id=user_id)
                documents = [{"document_id": record["document_id"], "file_name": record["file_name"]} for record in result]
                logger.debug(f"Retrieved documents for user_id {user_id}: {documents}")
                return documents
        except Exception as e:
            logger.error(f"Failed to retrieve documents for user_id {user_id}: {str(e)}", exc_info=True)
            raise

    def get_conversation_history(self, user_id: str) -> str:
        try:
            response = self.supabase.table("conversations").select("message, sender").eq("user_id", user_id).order("created_at").execute()
            history = "\n".join([f"{r['sender']}: {r['message']}" for r in response.data[-10:]])  # Last 10 messages
            logger.debug(f"Conversation history for user_id {user_id}: {history}")
            return history
        except Exception as e:
            logger.error(f"Failed to get conversation history for user_id {user_id}: {str(e)}", exc_info=True)
            return ""

    async def detect_handoff(self, message: str) -> bool:
        try:
            prompt = f"""
            Determine if the following user message indicates a request for human assistance or handoff.
            Examples of handoff triggers: "talk to a person", "human help", "escalate", "contact a volunteer".
            Message: {message}
            Return "true" if a handoff is requested, "false" otherwise.
            """
            response = await self.llm.acall(prompt)
            result = response.content.strip().lower() == "true"
            logger.debug(f"Handoff detection for message '{message}': {result}")
            return result
        except Exception as e:
            logger.error(f"Handoff detection failed: {str(e)}", exc_info=True)
            return False

    async def summarize_conversation(self, history: str) -> str:
        try:
            prompt = f"""
            Summarize the following conversation history in 2-3 sentences, focusing on the user's main concerns or questions:
            {history}
            """
            response = await self.llm.acall(prompt)
            summary = response.content.strip()
            logger.debug(f"Conversation summary: {summary}")
            return summary
        except Exception as e:
            logger.error(f"Conversation summarization failed: {str(e)}", exc_info=True)
            return "Unable to summarize conversation."

    async def match_volunteer(self, user_id: str, user_message: str) -> Dict:
        try:
            # Get user profile
            user_profile = self.supabase.table("profiles").select("political_standpoint, location").eq("user_id", user_id).execute().data[0]
            user_embedding = user_profile["political_standpoint"]
            user_location = user_profile["location"]

            # Vector search for similar political standpoint
            similar_profiles = self.supabase.table("profiles").select("user_id, email, location").neq("user_id", user_id).execute()
            best_match = None
            min_distance = float("inf")
            for profile in similar_profiles.data:
                if profile["political_standpoint"]:
                    # Compute cosine distance (simplified, using pgvector directly would be better)
                    response = self.supabase.rpc("cosine_distance", {
                        "id": profile["user_id"],
                        "query_embedding": user_embedding
                    }).execute()
                    distance = response.data[0]["distance"]
                    if distance < min_distance and profile["role"] == "volunteer":
                        min_distance = distance
                        best_match = profile

            # Neo4j: Check location proximity and campaign participation
            if best_match:
                with self.neo4j_driver.session() as session:
                    result = session.run("""
                        MATCH (u:User {user_id: $user_id})-[:LOCATED_IN]->(l:Location)
                        MATCH (v:User {user_id: $volunteer_id})-[:LOCATED_IN]->(vl:Location)
                        MATCH (v)-[:PARTICIPATES_IN]->(c:Campaign)
                        WHERE l.name = $user_location AND vl.name = $volunteer_location
                        RETURN v.user_id AS user_id, v.email AS email
                    """, user_id=user_id, volunteer_id=best_match["user_id"],
                        user_location=user_location, volunteer_location=best_match["location"])
                    match = result.single()
                    if match:
                        logger.info(f"Matched volunteer: {match['email']}")
                        return {"user_id": match["user_id"], "email": match["email"]}
            logger.warning(f"No suitable volunteer found for user_id {user_id}")
            return None
        except Exception as e:
            logger.error(f"Volunteer matching failed for user_id {user_id}: {str(e)}", exc_info=True)
            return None

    async def handle_chat(self, websocket: WebSocket, user_id: str, email: str):
        try:
            # Initialize session
            session_state = {"last_message": "", "conversation_id": None}
            conversation_id = self.supabase.table("conversations").insert({
                "user_id": user_id,
                "message": "Chat started",
                "sender": "bot"
            }).execute().data[0]["conversation_id"]
            session_state["conversation_id"] = str(conversation_id)
            self.supabase.table("sessions").insert({
                "user_id": user_id,
                "conversation_id": conversation_id,
                "session_state": session_state
            }).execute()
            logger.debug(f"Session initialized for user_id {user_id}, conversation_id {conversation_id}")

            # Get user-related documents from Neo4j
            documents = self.get_user_documents(user_id)
            context = f"Related documents: {', '.join([doc['file_name'] for doc in documents])}"

            while True:
                # Receive user message
                user_message = await websocket.receive_text()
                logger.debug(f"Received message from {email}: {user_message}")
                session_state["last_message"] = user_message

                # Store user message
                self.supabase.table("conversations").insert({
                    "user_id": user_id,
                    "message": user_message,
                    "sender": "user",
                    "conversation_id": conversation_id
                }).execute()
                logger.debug(f"Stored user message for user_id {user_id}")

                # Update session state
                self.supabase.table("sessions").update({
                    "session_state": session_state,
                    "updated_at": "now()"
                }).eq("session_id", conversation_id).execute()

                # Check for handoff
                if await self.detect_handoff(user_message):
                    history = self.get_conversation_history(user_id)
                    summary = await self.summarize_conversation(history)
                    volunteer = await self.match_volunteer(user_id, user_message)
                    if volunteer:
                        await self.email_service.send_notification(
                            volunteer["email"],
                            "Handoff Request",
                            f"A user needs assistance. Summary: {summary}"
                        )
                        response = f"Handoff initiated. A volunteer ({volunteer['email']}) has been notified."
                    else:
                        response = "No suitable volunteer found. Please try again later."
                else:
                    # Run hybrid search
                    try:
                        response = self.qa_chain.run(f"{context}\nUser query: {user_message}")
                    except Exception as e:
                        logger.error(f"QA chain failed: {str(e)}", exc_info=True)
                        response = "Sorry, I couldn't process your query. Please try again."

                # Send bot response
                await websocket.send_text(response)
                logger.debug(f"Sent bot response to {email}: {response}")

                # Store bot response
                self.supabase.table("conversations").insert({
                    "user_id": user_id,
                    "message": response,
                    "sender": "bot",
                    "conversation_id": conversation_id
                }).execute()
                logger.debug(f"Stored bot response for user_id {user_id}")

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user_id {user_id}")
            self.supabase.table("sessions").update({
                "session_state": session_state,
                "updated_at": "now()"
            }).eq("session_id", conversation_id).execute()
        except Exception as e:
            logger.error(f"Chat error for user_id {user_id}: {str(e)}", exc_info=True)
            await websocket.send_json({"error": str(e)})