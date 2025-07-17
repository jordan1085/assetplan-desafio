import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from src.config.settings import settings
from src.api.services.agent_service import AgentService
from src.api.endpoint.chat import create_api_router
from src.config.logging import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manejador del ciclo de vida de la aplicación FastAPI.
    """
    logger.info("Iniciando la aplicación...")
    
    checkpointer_context = AsyncPostgresSaver.from_conn_string(settings.POSTGRES_URL)
    memory_saver = await checkpointer_context.__aenter__()
    
    try:
        await memory_saver.setup()
        logger.info("Checkpointer de base de datos configurado.")
        
        await AgentService.initialize_agent_workflow(memory_saver)
        logger.info("Workflow del agente inicializado.")
        
        yield 

    finally:
        await checkpointer_context.__aexit__(None, None, None)
        AgentService.agent = None

app = FastAPI(
    title=settings.API_TITLE,
    lifespan=lifespan,
)

api_router = create_api_router()
app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=True
    )