import chromadb
from chromadb.utils import embedding_functions
from chromadb.config import Settings as ChromaSettings
from src.core.config import settings
from src.core.logging import logger

def get_embedding_function(name: str):
    """Devuelve un objeto de función de embedding basado en el nombre."""
    if name == "openai":
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.OPENAI_API_KEY,
            model_name=settings.OPENAI_EMBEDDINGS_MODEL
        )
    raise ValueError(f"Función de embedding desconocida: {name}")

def get_chroma_client():
    """Crea y devuelve un cliente ChromaDB configurado."""

    if settings.CHROMA_CLIENT_TYPE == "cloud":

        return chromadb.HttpClient(
            host="api.trychroma.com",
            ssl=True,
            tenant=settings.CHROMA_TENANT,
            database=settings.CHROMA_DATABASE,
            headers={'x-chroma-token': settings.CHROMA_API_KEY}
        )

    elif settings.CHROMA_CLIENT_TYPE == "http":
    
        chroma_native_settings = ChromaSettings()

        if settings.CHROMA_SERVER_AUTH_PROVIDER and settings.CHROMA_SERVER_CREDENTIALS:
            chroma_native_settings = ChromaSettings(
                chroma_client_auth_provider=settings.CHROMA_SERVER_AUTH_PROVIDER,
                chroma_client_auth_credentials=settings.CHROMA_SERVER_CREDENTIALS
            )

        logger.info(f"Inicializando Chroma HttpClient en host: {settings.CHROMA_HOST}:{settings.CHROMA_PORT}")
        return chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
            ssl=settings.CHROMA_SSL,
            settings=chroma_native_settings
        )
    else:
        raise ValueError(f"Tipo de cliente Chroma no soportado: {settings.CHROMA_CLIENT_TYPE}")

def get_chroma_collection(collection_name: str, embedding_function_name: str = "openai"):
    """
    Obtiene o crea una colección en ChromaDB.
    """
    client = get_chroma_client()
    embedding_function = get_embedding_function(embedding_function_name)

    return client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_function
    )
