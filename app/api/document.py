from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from ..services.auth_service import AuthService
from ..services.document_service import DocumentService
from ..schemas.user import UserResponse
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(prefix="/document", tags=["document"])
auth_service = AuthService()
document_service = DocumentService()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        user = auth_service.supabase.auth.get_user(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        profile = await auth_service.get_profile(str(user.user.id))
        if profile["role"] != "admin":
            raise HTTPException(status_code=403, detail="Only admins can access this endpoint")
        return {"user_id": str(user.user.id), "email": user.user.email}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/upload", response_model=dict)
async def upload_pdf(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    try:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        result = await document_service.upload_pdf(file, current_user["user_id"])
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))