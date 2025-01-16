import os
from motor.motor_asyncio import AsyncIOMotorClient
# from dotenv import load_dotenv
from datetime import datetime
from core.handlers.env_handler import env
# from base.exception import DatabaseConnectionError

mongo_uri = env.mongo["uri"]

class MongoClient:
    def __init__(self):
        self.client = AsyncIOMotorClient(mongo_uri)

    async def ping(self):
        """Ping Skyflow database and return if no exceptions."""
        try:
            db_name = "devarno"
            db = self.client.get_database(db_name)
            ping_response = await db.command("ping")
            if int(ping_response["ok"]) != 1:
                raise Exception(f"Problem connecting to cluster: {db_name}")
        except Exception as e:
            raise Exception(details=str(e)) # DB connection error
        finally:
            print(f"Database [{db_name}] connected successfully")
            return db

    async def close(self):
        """Close MongoDB client"""
        self.client.close()
        print("MongoDB client closed")

    def get_client(self):
        """Returns the initialized Mongo client"""
        return self.client

    def get_database(self, db_name: str):
        """Retrieve a specific database by name."""
        return self.client.get_database(db_name)

    @staticmethod
    def construct_kudos_data(fliers: list[dict], user_did: str, timestamp: datetime) -> dict:
        """Construct Kudos data for insertion."""
        return {
            "dids": [f"{flier['profile']['did']}::{i + 1}" for i, flier in enumerate(fliers)],
            "user": user_did,
            "date": timestamp,
        }

    @staticmethod
    def construct_clout_data(popular_posts: list[dict], user_did: str, timestamp: datetime) -> dict:
        """Construct Clout data for insertion."""
        return {
            "uris": [f"{post['uri']}::{i + 1}" for i, post in enumerate(popular_posts)],
            "user": user_did,
            "date": timestamp,
        }