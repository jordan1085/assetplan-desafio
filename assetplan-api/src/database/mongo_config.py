from pymongo import MongoClient
from src.core.config import settings

db_name = settings.MONGO_DB_NAME
mongo_url = settings.MONGO_URL
mongo_collection_name = settings.MONGO_COLLECTION_NAME


mongo_client = MongoClient(mongo_url)

def initialize_database():
    """
    Initializes the database and returns the database client.
    """
    try:
        return mongo_client[db_name]
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

def get_mongo_client():
    """
    Returns the MongoDB client instance.
    """
    return mongo_client

def get_collection():
    """
    Returns the MongoDB collection instance.
    """
    db = initialize_database()
    return db[mongo_collection_name]