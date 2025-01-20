import os
import jwt 
from typing import Optional, Union
from datetime import datetime, timedelta, timezone
from enum import Enum
from fastapi.exceptions import HTTPException

from core.base.exception import ServiceLevelError

class TokenPermission(Enum):
    ChangePreferences="change_preferences"
    VerifyEmail="verify_email"

class TokenService:
    def __init__(self, secret_key: str, algorithm: str):
        self.secret_key = secret_key
        self.algorithm = algorithm
        if not self.secret_key or not self.algorithm:
            raise ValueError("JWT_SECRET_KEY and ALGORITHM expected in .env")
        self.token_duration = timedelta(days=7)
    
    async def generate_reach_token(self, 
            uid: str,
            permission: TokenPermission,
            email: Optional[str] = None,
        ) -> str:
        """Generate a secure reach token with specific payload and signiature"""
        timestamp = datetime.now(timezone.utc)
        expire_time = timestamp + self.token_duration
        payload = {
            "sub": uid,
            "iat": timestamp,
            "exp": expire_time,
            "perm": permission.value,
            
        }
        if email is not None:
            payload["email"] = email
        try:
            return jwt.encode(
                payload,
                self.secret_key,
                algorithm=self.algorithm
            )
        except Exception as e:
            raise ServiceLevelError(message={"generate_reach_token": e})
                
    async def verify_reach_token(self, 
        token: str, 
        permissions: list[TokenPermission],
    ) -> dict:
        """Verify token and required permissions."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            token_permission = payload.get("perm")
            if token_permission and token_permission in [perm.value for perm in permissions]:
                return {
                    "uid": payload["sub"],
                    "email": payload.get("email"),
                }
            raise ServiceLevelError(message="Insufficient permissions")
        except jwt.ExpiredSignatureError:
            raise ServiceLevelError(message="Token expired")
        except jwt.InvalidTokenError:
            raise ServiceLevelError(message="Invalid token")

    
def new_token_service(secret_key: str, algorithm: str) -> TokenService:
    return TokenService(secret_key, algorithm)