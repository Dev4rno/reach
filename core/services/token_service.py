from datetime import datetime, timedelta, timezone
import jwt
from typing import Optional
import os
from fastapi import HTTPException

class TokenService:
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY")
        if not self.secret_key:
            raise ValueError("JWT_SECRET_KEY must be set in environment variables")
        self.algorithm = "HS256"
        self.token_duration = timedelta(days=7)
    
    async def generate_reach_token(self, uid: str) -> str:
        """
        Generate a secure unsubscribe token.
        
        Args:
            email: User's email address
            additional_data: Optional dictionary of additional data to include in token
            
        Returns:
            str: JWT token
        """
        timestamp = datetime.now(timezone.utc)
        expire_time = timestamp + self.token_duration
        payload = {
            "sub": uid,
            "type": "reach",
            "iat": timestamp,
            "exp": expire_time,
            "jti": os.urandom(16).hex()
        }    
        try:
            return jwt.encode(
                payload,
                self.secret_key,
                algorithm=self.algorithm
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error generating token: {str(e)}"
            )
        
    async def verify_reach_token(self, token: str, uid: str) -> str:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("sub") == uid and payload.get("type") == "reach":
                return payload.get("sub")
            return None
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
