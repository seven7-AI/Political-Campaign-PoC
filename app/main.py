import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI
from .api.auth import router as auth_router
from .api.document import router as document_router
from .api.chat import router as chat_router

app = FastAPI(title="Political Campaign POC")

app.include_router(auth_router)
app.include_router(document_router)
app.include_router(chat_router)

@app.get("/")
async def root():
    return {"message": "Political Campaign POC API"}