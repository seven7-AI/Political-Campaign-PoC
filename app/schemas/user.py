from pydantic import BaseModel, EmailStr, Field
from enum import Enum
from typing import Optional
from uuid import UUID

class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"
    VOLUNTEER = "volunteer"

class UserBase(BaseModel):
    email: EmailStr
    role: Role
    location: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    location: Optional[str] = None
    political_standpoint: Optional[str] = None  # Text input for non-volunteers

class UserResponse(UserBase):
    user_id: UUID
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class QuestionnaireResponseCreate(BaseModel):
    question_id: int
    answer: str = Field(..., min_length=10)

class QuestionnaireResponseResponse(BaseModel):
    response_id: UUID
    user_id: UUID
    question_id: int
    answer: str
    created_at: str

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str