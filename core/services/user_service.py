from typing import Optional
from fastapi import HTTPException, status
from core.base.models import User, EmailPreferences
from core.repositories.user_repository import UserRepository
from core.base.exception import ServiceLevelError, DataNotFoundError

class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def create_user(self, email: str, name: Optional[str] = None, source: Optional[str] = None) -> User:
        """Create a new user."""
        existing_user = await self.repository._get_user_by_email(email)
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email already exists.")        
        user = User(email=email, name=name, source=source)
        return await self.repository._create_user(user)
    
    async def get_user(self, identifier: str) -> User:
        """
        Get a user by their email or UID.
        
        If the identifier contains an '@' symbol, it is treated as an email.
        Otherwise, it is treated as a UID.
        """
        try:
            if "@" in identifier and len(identifier.split("@")) == 2:
                user = await self.repository._get_user_by_email(identifier)
            else:
                user = await self.repository._get_user_by_uid(identifier)
            return user
        except Exception as e:
            raise ServiceLevelError(message={"get_user": str(e)})


    async def update_user(self, 
        uid: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        preferences: Optional[dict] = None,
    ) -> User:
        """Update a user document."""
        update_data = {}
        if name:
            update_data["name"] = name
        if email:
            update_data["email"] = email
        if preferences:
            update_data["preferences"] = preferences
        updated_user = await self.repository._update_user(uid, update_data)
        if not updated_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        return updated_user

    async def unsubscribe_user(self, uid: str) -> User:
        """Unsubscribe a user (set all email preferences to False)"""
        update_data = {
            "preferences": {
                "marketing": False,
                "product": False,
                "content": False
            }
        }
        user = await self.repository._update_user(uid, update_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="User not found."
            )
        return user
    
    async def resubscribe_user(self, uid: str) -> User:
        """Resubscribe a user (set all email preferences to default)."""
        update_data = {"preferences": EmailPreferences().model_dump()}
        user = await self.repository._update_user(uid, update_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="User not found."
            )
        return user

    async def delete_user(self, uid: str) -> bool:
        """Delete a user by UID."""
        user_deleted = await self.repository._delete_user(uid)
        if not user_deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        return True

def new_user_service(repository: UserRepository) -> UserService:
    return UserService(repository)