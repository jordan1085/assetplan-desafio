from typing import Optional
from fastapi import APIRouter, Form, HTTPException
from src.config.logging import logger
from src.api.models.responses import ChatResponse
from src.api.services.agent_service import AgentService


def create_api_router() -> APIRouter:
    """Router para endpoints de chat"""
    router = APIRouter(prefix="/chat", tags=["Chat"])
    
    @router.post("/")
    async def chat(
        message: str = Form(...),
        user_id: str = Form(...),
        thread_id: Optional[str] = Form(None),
    ):
        try:
            if not thread_id:
                session = await AgentService.create_chat_session(user_id)
                thread_id = session["thread_id"]
            
            response_data = await AgentService.process_message(
                message, 
                thread_id,
                user_id,
            )

            return ChatResponse(**response_data)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=500, detail="Ocurrió un error.")
    
    return router