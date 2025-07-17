from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "AI Agent Lab - API Service"

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    CHROMA_CLIENT_TYPE: str = "http"  # ephemeral, persistent, http, cloud
    CHROMA_DATA_DIR: Optional[str] = "./data" # For persistent client
    CHROMA_HOST: Optional[str] = "chromadb" # For http client
    CHROMA_PORT: Optional[str] = "8000" # For http client
    CHROMA_SSL: bool = False # For http client
    CHROMA_SERVER_AUTH_PROVIDER: Optional[str] = None
    CHROMA_SERVER_CREDENTIALS: Optional[str] = None
    CHROMA_COLLECTION_NAME: str = "properties"  # Name of the collection for agent documents
    
    # For cloud client
    CHROMA_TENANT: Optional[str] = None
    CHROMA_DATABASE: Optional[str] = None
    CHROMA_API_KEY: Optional[str] = None
    
    OPENAI_API_KEY: Optional[str] = None
    COHERE_API_KEY: Optional[str] = None
    OPENAI_EMBEDDINGS_MODEL: str = "text-embedding-3-small"


    # PostgreSQL
    POSTGRES_URL: str = "postgresql://postgres:admin@langgraph_memory:5432/client_memory"


    # MongoDB
    MONGO_URL: str = "mongodb://mongo:27017"
    MONGO_DB_NAME: str = "assetplan"
    MONGO_COLLECTION_NAME: str = "assetplan"


    # Add other API keys if needed for other embedding functions
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()