from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import List, Optional
from app.services.auth_service import AuthService
from app.services.document_service import DocumentService
from app.services.chat_service import ChatService
from app.services.email_service import EmailService
from app.api.document import router as document_router
from app.api.chat import router as chat_router
import os
from dotenv import load_dotenv
import logging
from app.custom_swagger import configure_custom_swagger

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# OAuth2 scheme for JWT
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# OpenAPI tags metadata
tags_metadata = [
    {
        "name": "Authentication",
        "description": "Handles user registration, login, profile management, and volunteer questionnaire. Uses Supabase for authentication and user data storage."
    },
    {
        "name": "Document",
        "description": "Manages document uploads and processing. Stores PDFs in Supabase storage and embeddings in document_embeddings."
    },
    {
        "name": "Chat",
        "description": "Provides WebSocket-based chat functionality powered by LangChain and OpenAI for conversational responses."
    },
    {
        "name": "Handoff",
        "description": "Manages WebSocket handoff to human volunteers, with notifications via Resend API."
    }
]

# Initialize FastAPI app with custom metadata
app = FastAPI(
    title="Political Campaign API",
    description="""
    A FastAPI-based API for a political campaign platform, integrating:
    - **Supabase**: Authentication, user profiles, document storage, and session management.
    - **Neo4j**: Graph database for campaign and user relationships.
    - **OpenAI**: Powers chat, handoff detection, and embeddings for political standpoints.
    - **Resend API**: Sends email notifications for handoffs and user actions.

    ### Backend Workflow
    1. **Authentication**: Users register/login via Supabase. Roles (admin, user, volunteer) are stored in the `profiles` table.
    2. **Document Processing**: Admins upload PDFs via `/document/upload`, stored in Supabase storage, with embeddings in `document_embeddings`.
    3. **Chat**: WebSocket endpoint `/chat/ws` for real-time queries, using LangChain for vector search and OpenAI for responses.
    4. **Handoff**: Detects user intent for human assistance, matches volunteers using Supabase/pgvector and Neo4j, and notifies via Resend API.
    """,
    version="1.0.0",
    contact={
        "name": "Campaign Team",
        "email": "arapbiisubmissions@gmail.com",
        "url": "https://your-campaign-site.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    openapi_tags=tags_metadata
)

# Mount static files for logo
app.mount("/static", StaticFiles(directory="static"), name="static")

# Custom OpenAPI schema with logo
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
        servers=[
            {"url": "http://localhost:8000", "description": "Local Development Server"},
            {"url": "https://your-ec2-public-dns:8000", "description": "EC2 Production Server"}
        ]
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "/static/logo.png",
        "altText": "Political Campaign Logo"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Configure custom Swagger UI
configure_custom_swagger(app)

# Pydantic models
class User(BaseModel):
    email: str
    password: str
    role: str
    location: str

class ProfileUpdate(BaseModel):
    location: Optional[str] = None

class QuestionnaireResponse(BaseModel):
    question_id: int
    answer: str

# Initialize services
auth_service = AuthService()
document_service = DocumentService()
chat_service = ChatService()
email_service = EmailService()

# Authentication Endpoints
@app.post("/auth/register", tags=["Authentication"], summary="Register a new user")
async def register(user: User):
    """Register a new user with email, password, role, and location. Stores in Supabase and sends welcome email via Resend API."""
    try:
        user_data = await auth_service.register_user(user)
        await email_service.send_notification(user.email, "Welcome to the Campaign", "Thank you for registering!")
        return user_data
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/login", tags=["Authentication"], summary="Login and get JWT token")
async def login(user: User):
    """Authenticate user with email and password. Returns JWT token for accessing protected endpoints."""
    try:
        return await auth_service.login_user(user.email, user.password)
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))

@app.get("/auth/profile", tags=["Authentication"], summary="Get user profile")
async def get_profile(current_user: dict = Depends(oauth2_scheme)):
    """Retrieve the authenticated user's profile from Supabase."""
    try:
        user = await auth_service.get_current_user(current_user)
        return await auth_service.get_profile(user["user_id"])
    except Exception as e:
        logger.error(f"Get profile failed: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))

@app.put("/auth/profile", tags=["Authentication"], summary="Update user profile")
async def update_profile(update_data: ProfileUpdate, current_user: dict = Depends(oauth2_scheme)):
    """Update user profile information, such as location, in Supabase."""
    try:
        user = await auth_service.get_current_user(current_user)
        return await auth_service.update_profile(user["user_id"], update_data)
    except Exception as e:
        logger.error(f"Update profile failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/volunteer/questionnaire", tags=["Authentication"], summary="Submit volunteer questionnaire")
async def submit_questionnaire(responses: List[QuestionnaireResponse], current_user: dict = Depends(oauth2_scheme)):
    """Submit volunteer questionnaire responses, stored in Supabase."""
    try:
        user = await auth_service.get_current_user(current_user)
        return await auth_service.submit_questionnaire(user["user_id"], responses)
    except Exception as e:
        logger.error(f"Questionnaire submission failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/auth/volunteer/questionnaire", tags=["Authentication"], summary="Get volunteer questionnaire")
async def get_questionnaire(current_user: dict = Depends(oauth2_scheme)):
    """Retrieve volunteer questionnaire responses from Supabase."""
    try:
        user = await auth_service.get_current_user(current_user)
        return await auth_service.get_questionnaire_responses(user["user_id"])
    except Exception as e:
        logger.error(f"Get questionnaire failed: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))

# Include routers for document and chat
app.include_router(document_router)
app.include_router(chat_router)