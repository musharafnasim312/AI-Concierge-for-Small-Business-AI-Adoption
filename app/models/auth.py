from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Token data model"""
    username: Optional[str] = None

class UserCreate(BaseModel):
    """User creation model"""
    username: str
    password: str

class UserInDB(UserCreate):
    """User model as stored in database"""
    hashed_password: str
