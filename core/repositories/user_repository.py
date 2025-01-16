from motor.motor_asyncio import AsyncIOMotorCollection
from typing import Optional
from pymongo.errors import DuplicateKeyError
from core.base.models import User
from datetime import datetime, timezone

class UserRepository:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def _create_user(self, user: User) -> User:
        """Insert a new user into the database."""
        try:
            user_dict = user.model_dump()
            _ = await self.collection.insert_one(user_dict)
            
            # user.uid = str(result.inserted_id)
            return await self._get_user_by_email(user.email)
        except DuplicateKeyError:
            raise ValueError("A user with that email already exists")

    async def _get_user_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by email."""
        user_data = await self.collection.find_one({"email": email})
        if user_data:
            return User(**user_data)
        return None

    async def _get_user_by_uid(self, uid: str) -> Optional[User]:
        """Retrieve a user by UID."""
        user_data = await self.collection.find_one({"uid": uid})
        if user_data:
            return User(**user_data)
        return None

    async def _update_user(self, uid: str, update_data: dict) -> Optional[User]:
        """Update user details by UID."""
        update_data["updatedAt"] = datetime.now(timezone.utc)
        result = await self.collection.update_one(
            {"uid": uid}, {"$set": update_data}
        )
        if result.modified_count > 0:
            return await self._get_user_by_uid(uid)
        return None

    async def _delete_user(self, uid: str) -> bool:
        """Delete a user by UID."""
        result = await self.collection.delete_one({"uid": uid})
        return result.deleted_count > 0
