from datetime import datetime
from fastapi import APIRouter, HTTPException, Form
from src.services.user_service import user_service
from src.services.session_service import session_service
from src.core.logging import logger

def create_users_router() -> APIRouter:
    """Router para endpoints de gestión de usuarios"""
    router = APIRouter(prefix="/user", tags=["Users"])
    
    @router.post("/")
    async def create_or_get_user(
        email: str = Form(None),
        username: str = Form(None),
    ):
        try:
            user = user_service.create_or_get_user(email, username)

            return user
        
        except Exception as e:
            logger.error(f"❌ Error creando/obteniendo usuario: {e}")
            raise HTTPException(status_code=500, detail=f"Error con usuario: {str(e)}")
    
    @router.post("/{user_id}/sessions")
    async def create_user_session(user_id: int):
        """
        Crea una nueva sesión de chat para un usuario.
        """
        try:
            session = session_service.create_chat_session(user_id)
            
            return session
            
        except Exception as e:
            logger.error(f"❌ Error creando sesión para usuario {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Error interno del servidor")
        
    return router
