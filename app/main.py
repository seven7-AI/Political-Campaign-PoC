import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI
from .api.auth import router as auth_router

app = FastAPI(title="Political Campaign POC")

app.include_router(auth_router)

@app.get("/")
async def root():
    return {"message": "Political Campaign POC API"}