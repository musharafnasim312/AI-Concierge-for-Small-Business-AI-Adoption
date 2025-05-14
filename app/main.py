from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address

from .routers import auth, concierge
from .core.config import settings

app = FastAPI(title="AI Concierge")
limiter = Limiter(key_func=get_remote_address)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, tags=["auth"])
app.include_router(concierge.router, prefix="/concierge", tags=["concierge"], dependencies=[Depends(auth.get_current_user)])

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
