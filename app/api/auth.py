from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from fastapi.security import OAuth2PasswordBearer
from supabase import Client
from ..services.auth_service import AuthService
from ..schemas.user import UserCreate, UserResponse, UserUpdate, QuestionnaireResponseCreate, QuestionnaireResponseResponse, TokenResponse
from typing import List
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
auth_service = AuthService()

def get_supabase_client() -> Client:
    return auth_service.supabase

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        user = auth_service.supabase.auth.get_user(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"user_id": str(user.user.id), "email": user.user.email}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate):
    try:
        result = await auth_service.register_user(user)
        # Ensure created_at is included in the response
        response_data = {
            "user_id": result["user_id"],
            "email": result["email"],
            "role": user.role,
            "location": user.location,
            "created_at": datetime.now().isoformat(),  # Generate current timestamp using isoformat
            "updated_at": datetime.now().isoformat()   # Generate current timestamp using isoformat
        }
        return UserResponse(**response_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login_user(request: Request):
    try:
        data = await request.json()
        email = data.get("email")
        password = data.get("password")
        token = await auth_service.login_user(email, password)
        return token
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: dict = Depends(get_current_user)):
    try:
        profile = await auth_service.get_profile(current_user["user_id"])
        return UserResponse(**profile)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/profile", response_model=UserResponse)
async def update_profile(user: UserUpdate, current_user: dict = Depends(get_current_user)):
    try:
        profile = await auth_service.update_profile(current_user["user_id"], user)
        return UserResponse(**profile)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/volunteer/questionnaire")
async def submit_questionnaire(responses: List[QuestionnaireResponseCreate], current_user: dict = Depends(get_current_user)):
    try:
        profile = await auth_service.get_profile(current_user["user_id"])
        if profile["role"] != "volunteer":
            raise HTTPException(status_code=403, detail="Only volunteers can submit questionnaires")
        result = await auth_service.submit_questionnaire(current_user["user_id"], responses)
        return {"message": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/volunteer/questionnaire", response_model=List[QuestionnaireResponseResponse])
async def get_questionnaire_responses(current_user: dict = Depends(get_current_user)):
    try:
        profile = await auth_service.get_profile(current_user["user_id"])
        if profile["role"] != "volunteer":
            raise HTTPException(status_code=403, detail="Only volunteers can view questionnaires")
        responses = await auth_service.get_questionnaire_responses(current_user["user_id"])
        return [QuestionnaireResponseResponse(**response) for response in responses]
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))