import os
from supabase import create_client, Client
from openai import OpenAI
from dotenv import load_dotenv
import logging
import PyPDF2
from io import BytesIO
from fastapi import UploadFile

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("document_service.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self):
        load_dotenv()
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        if not supabase_url or not supabase_key:
            logger.error(f"SUPABASE_URL or SUPABASE_ANON_KEY not set: URL={supabase_url}, Key={'set' if supabase_key else 'not set'}")
            raise ValueError("Supabase configuration missing")
        self.supabase: Client = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized")
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        logger.info("OpenAI client initialized")

    async def upload_pdf(self, file: UploadFile, user_id: str) -> dict:
        try:
            # Read PDF content
            file_content = await file.read()
            file_name = file.filename
            logger.debug(f"Processing PDF: {file_name}, Size: {len(file_content)} bytes")

            # Extract text from PDF
            pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
            logger.debug(f"Extracted text length: {len(text)} characters")

            # Generate embedding
            embedding_response = self.openai.embeddings.create(
                input=text[:8192],  # Truncate to OpenAI's max token limit
                model="text-embedding-ada-002"
            )
            embedding = embedding_response.data[0].embedding
            logger.debug(f"Generated embedding for {file_name}")

            # Upload to Supabase Storage
            storage_path = f"pdfs/{file_name}"
            self.supabase.storage.from_("pdfs").upload(storage_path, file_content)
            logger.info(f"Uploaded PDF to Supabase Storage: {storage_path}")

            # Store metadata and embedding
            document_data = {
                "file_name": file_name,
                "file_path": storage_path,
                "uploaded_by": user_id,
                "embedding": embedding
            }
            response = self.supabase.table("document_embeddings").insert(document_data).execute()
            logger.debug(f"Inserted document metadata: {document_data}")
            return {
                "document_id": response.data[0]["document_id"],
                "file_name": file_name,
                "message": "PDF uploaded successfully"
            }
        except Exception as e:
            logger.error(f"Failed to upload PDF {file_name}: {str(e)}", exc_info=True)
            raise