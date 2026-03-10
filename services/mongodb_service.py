import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_DB_URI")
DB_NAME = "cliniq_analytics"

class MongoDBService:
    def __init__(self):
        self.client = None
        self.db = None
        if MONGO_URI:
            self.client = AsyncIOMotorClient(MONGO_URI)
            self.db = self.client[DB_NAME]
            print("MongoDB client initialized.")

    async def log_event(self, event_type, data):
        """Log a clinical or system event to MongoDB for persistent analytics."""
        if not self.db:
            return
        
        try:
            collection = self.db["events"]
            event_doc = {
                "event_type": event_type,
                "timestamp": datetime.utcnow(),
                "data": data
            }
            await collection.insert_one(event_doc)
        except Exception as e:
            print(f"MongoDB logging error: {e}")

    async def log_activity(self, staff_name, action_type, description, patient_id=None, metadata=None, timestamp=None):
        """Log staff activity to MongoDB."""
        if not self.db:
            return
        
        try:
            collection = self.db["activities"]
            activity_doc = {
                "staff_name": staff_name,
                "action_type": action_type,
                "description": description,
                "patient_id": patient_id,
                "metadata": metadata or {},
                "timestamp": timestamp or datetime.utcnow()
            }
            await collection.insert_one(activity_doc)
        except Exception as e:
            print(f"MongoDB logging error: {e}")

# Global instance
mongo_service = MongoDBService()
