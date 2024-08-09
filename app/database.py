# database.py
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

class Database:
    client: AsyncIOMotorClient = None

db = Database()
main_db = Database()

def connect_to_mongo():
    db.client = AsyncIOMotorClient(settings.MONGO_DB_URL,maxPoolSize=settings.MAX_POOL_SIZE)
    print("Connected to MongoDB")

def close_mongo_connection():
    db.client.close()
    print("Connection to MongoDB closed")

def get_database():
    return db.client[settings.DATABASE_NAME]
