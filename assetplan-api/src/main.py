from fastapi import FastAPI
from src.core.config import settings
from contextlib import asynccontextmanager
from src.core.logging import logger
from src.api.endpoints import router
from src.database.postgres_config import initialize_database
from src.database.chroma_config import get_chroma_client, get_chroma_collection

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Maneja la lógica de inicio y apagado de la aplicación.
    """
    logger.info(f"Iniciando {settings.APP_NAME}...")
    
    try:
        # Llama a la única función de inicialización de Postgres
        initialize_database()
        logger.info("Base de datos inicializada correctamente.")
    except Exception as e:
        logger.critical(f"No se pudo inicializar la base de datos. Error: {e}", exc_info=True)
        raise

    logger.info("Inicializando el cliente de ChromaDB.")
    try:
        # Inicializa el cliente de ChromaDB
        get_chroma_client()
        get_chroma_collection(settings.CHROMA_COLLECTION_NAME)
        logger.info("Cliente de ChromaDB y colección por defecto inicializados correctamente.")
    except Exception as e:
        logger.critical(f"No se pudo inicializar ChromaDB. Error: {e}", exc_info=True)
        raise

    yield

    logger.info(f"Apagando {settings.APP_NAME}...")


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan
)

api_router = router.create_api_router()
app.include_router(api_router)

@app.get("/", tags=["Root"])
async def read_root():
    logger.info("Se accedió al endpoint raíz.")
    return {"message": f"Bienvenido a {settings.APP_NAME}. Documentación en /docs o /redoc."}