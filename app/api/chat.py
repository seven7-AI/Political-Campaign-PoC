from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect
from ..services.auth_service import AuthService
from ..services.chat_service import ChatService
from fastapi.security import OAuth2PasswordBearer
import json

router = APIRouter(prefix="/chat", tags=["chat"])
auth_service = AuthService()
chat_service = ChatService()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(token: str) -> dict:
    try:
        user = auth_service.supabase.auth.get_user(token)
        if not user:
            raise Exception("Invalid token")
        return {"user_id": str(user.user.id), "email": user.user.email}
    except Exception as e:
        raise Exception(f"Authentication failed: {str(e)}")

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        # Receive JWT token
        token = await websocket.receive_text()
        user = await get_current_user(token)
        
        # Check for existing session
        session = chat_service.supabase.table("sessions").select("*").eq("user_id", user["user_id"]).order("updated_at", desc=True).limit(1).execute()
        if session.data:
            await websocket.send_text(f"Resuming session: {json.dumps(session.data[0]['session_state'])}")
        
        await chat_service.handle_chat(websocket, user["user_id"], user["email"])
    except WebSocketDisconnect:
        await websocket.close()
    except Exception as e:
        await websocket.send_json({"error": str(e)})
        await websocket.close()