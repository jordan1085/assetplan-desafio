import httpx
from typing import Dict, Any, Optional
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from src.agent.workflow import WorkflowBuilder
from src.config.logging import logger
from src.config.settings import settings

class AgentService:
    """Servicio para manejar operaciones del agente."""
    def __init__(self):
        self.agent = None
        self.workflow_builder = None
        self.active_threads = set()

    async def initialize_agent_workflow(self, memory_saver: AsyncPostgresSaver):
        try:
            self.workflow_builder = WorkflowBuilder(
                memory_saver=memory_saver
            )

            self.agent = await self.workflow_builder.build_agent_workflow()

        except Exception as e:
            logger.error(f"Error inicializando workflow del agente: {e}")
            raise
    
    async def invoke_agent(self, messages: list, thread_id: str, user_id: Optional[str] = None) -> dict:
        """Invoca al agente con los mensajes y parámetros dados"""
        if not self.agent:
            raise RuntimeError("Agente no inicializado")
        
        self.active_threads.add(thread_id)

        config = {"configurable": {"thread_id": thread_id}}
        
        input_data = {
            "messages": messages,
            "user_id": user_id,
        }

        try:
            result = await self.agent.ainvoke(input_data, config=config)
            
            return result
            
        except Exception as e:
            logger.error(f"Error inesperado al invocar al agente: {e}")
            raise

    async def process_message(self, message: str, thread_id: str, user_id: str) -> dict:
        """Procesa un mensaje de usuario y devuelve la respuesta completa formateada"""
        try:
            result = await self.invoke_agent(
                messages=[("human", message)], 
                thread_id=thread_id,
                user_id=user_id
            )
            
            response_text = str(result["messages"][-1].content)
        
            return {
                "type": "ai_response",
                "query": message,
                "response": response_text,
                "thread_id": thread_id
            }
                
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
            raise
    

    async def create_chat_session(self, user_id: int):
        """Crea una nueva sesión de chat para un usuario"""
        try:
            async with httpx.AsyncClient() as client:
                
                payload = {
                    "user_id": user_id
                }

                path = f"{settings.ASSETPLAN_API_URL}/user/{user_id}/sessions"

                response = await client.post(path, json=payload)
                response.raise_for_status()
    
                return response.json()
            
        except httpx.RequestError as exc:
            logger.error(f"Error al crear sesión para usuario {user_id}: {exc}")
            raise
     
        except Exception as e:
            logger.error(f"Error inesperado creando sesión para usuario {user_id}: {e}")
            raise

AgentService = AgentService()