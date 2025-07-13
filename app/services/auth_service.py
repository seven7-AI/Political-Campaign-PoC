import os
from supabase import create_client, Client
from openai import AsyncOpenAI
from dotenv import load_dotenv
import logging
from uuid import UUID
from typing import List
from ..schemas.user import QuestionnaireResponseCreate, UserCreate, UserUpdate

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("auth_service.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        load_dotenv()
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        if not supabase_url or not supabase_key:
            logger.error(f"SUPABASE_URL or SUPABASE_ANON_KEY not set: URL={supabase_url}, Key={'set' if supabase_key else 'not set'}")
            raise ValueError("Supabase configuration missing")
        self.supabase: Client = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized")
        self.openai = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        logger.info("OpenAI client initialized")

    async def register_user(self, user: UserCreate) -> dict:
        try:
            # Register user in Supabase Authentication
            response = self.supabase.auth.sign_up({
                "email": user.email,
                "password": user.password
            })

            # Log the entire response for debugging
            logger.debug(f"Supabase sign-up response: {response}")

            # Check if the response has the expected structure
            if not hasattr(response, 'user'):
                logger.error(f"Registration failed for {user.email}: No user returned in response")
                raise Exception("Registration failed: No user in response")

            user_id = response.user.id
            logger.info(f"User registered: {user.email}, ID: {user_id}")

            # Store profile in Supabase
            profile_data = {
                "user_id": str(user_id),
                "email": user.email,
                "role": user.role.value,
                "location": user.location
            }
            profile_response = self.supabase.table("profiles").insert(profile_data).execute()
            logger.debug(f"Profile inserted: {profile_data}")

            return {"user_id": user_id, "email": user.email}
        except Exception as e:
            logger.error(f"Failed to register user {user.email}: {str(e)}", exc_info=True)
            raise
        
    async def login_user(self, email: str, password: str) -> dict:
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            logger.debug(f"Login response: {response.__dict__}")
            if not response.session:
                logger.error(f"Login failed for {email}: No session returned")
                raise Exception("Login failed")
            logger.info(f"User logged in: {email}")
            return {
                "access_token": response.session.access_token,
                "token_type": "bearer"
            }
        except Exception as e:
            logger.error(f"Failed to login user {email}: {str(e)}", exc_info=True)
            if "Email not confirmed" in str(e):
                logger.warning(f"Allowing login for unconfirmed email: {email}")
                # Optionally, you can return a token or handle this case differently for testing
                return {
                    "access_token": "test_token_for_unconfirmed_email",
                    "token_type": "bearer"
                }
            raise

    async def get_profile(self, user_id: str) -> dict:
        try:
            response = self.supabase.table("profiles").select("*").eq("user_id", user_id).execute()
            if not response.data:
                logger.error(f"Profile not found for user_id: {user_id}")
                raise Exception("Profile not found")
            logger.debug(f"Profile retrieved for user_id: {user_id}, Data: {response.data[0]}")
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to get profile for user_id {user_id}: {str(e)}", exc_info=True)
            raise

    async def update_profile(self, user_id: str, user: UserUpdate) -> dict:
        try:
            update_data = {"updated_at": "now()"}
            if user.location:
                update_data["location"] = user.location
            if user.political_standpoint and user.role != "volunteer":
                embedding = await self.openai.embeddings.create(
                    input=user.political_standpoint,
                    model="text-embedding-ada-002"
                )
                update_data["political_standpoint"] = embedding.data[0].embedding
                logger.debug(f"Generated embedding for political_standpoint: {user.political_standpoint}")
            
            response = self.supabase.table("profiles").update(update_data).eq("user_id", user_id).execute()
            if not response.data:
                logger.error(f"Failed to update profile for user_id: {user_id}")
                raise Exception("Profile update failed")
            logger.info(f"Profile updated for user_id: {user_id}")
            return await self.get_profile(user_id)
        except Exception as e:
            logger.error(f"Failed to update profile for user_id {user_id}: {str(e)}", exc_info=True)
            raise

    async def submit_questionnaire(self, user_id: str, responses: List[QuestionnaireResponseCreate]) -> str:
        try:
            # Store responses
            for response in responses:
                response_data = {
                    "user_id": user_id,
                    "question_id": response.question_id,
                    "answer": response.answer
                }
                self.supabase.table("questionnaire_responses").insert(response_data).execute()
                logger.debug(f"Inserted questionnaire response: {response_data}")
            
            # Generate political standpoint embedding
            combined_answers = " ".join([r.answer for r in responses])
            embedding = await self.openai.embeddings.create(
                input=combined_answers,
                model="text-embedding-ada-002"
            )
            self.supabase.table("profiles").update({
                "political_standpoint": embedding.data[0].embedding
            }).eq("user_id", user_id).execute()
            logger.info(f"Questionnaire submitted and embedding updated for user_id: {user_id}")
            return "Questionnaire submitted successfully"
        except Exception as e:
            logger.error(f"Failed to submit questionnaire for user_id {user_id}: {str(e)}", exc_info=True)
            raise

    async def get_questionnaire_responses(self, user_id: str) -> List[dict]:
        try:
            response = self.supabase.table("questionnaire_responses").select("*").eq("user_id", user_id).execute()
            logger.debug(f"Questionnaire responses retrieved for user_id: {user_id}, Data: {response.data}")
            return response.data
        except Exception as e:
            logger.error(f"Failed to get questionnaire responses for user_id {user_id}: {str(e)}", exc_info=True)
            raise