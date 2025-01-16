from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from core.utils.str import random_id
from datetime import datetime, timezone


class EmailPreferences(BaseModel):
    marketing: bool = True
    product: bool = True
    content: bool = True


class User(BaseModel):
    """Pydantic model for credential validation"""
    uid: str = Field(default_factory=random_id)
    email: EmailStr
    name: Optional[str] = Field(None, min_length=2, max_length=60)
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: Optional[str] = Field(None, min_length=2, max_length=20)
    preferences: EmailPreferences = Field(default_factory=EmailPreferences)
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class UnsubscribeToken(BaseModel):
    email: EmailStr
    token: str

