import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, func
from src.core.config import settings
from src.models.chat_session import ChatSession
from src.models.user import User
from src.core.logging import logger

# Usa la misma configuración de base de datos que crud.py
engine = create_engine(settings.POSTGRES_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class SessionService:
    """Servicio para manejar operaciones de sesiones de chat usando SQLAlchemy"""
    
    def __init__(self):
        pass

    def create_chat_session(self, user_id: str) -> Dict[str, Any]:
        """Crea una nueva sesión de chat para un usuario"""
        db = SessionLocal()
        try:
            thread_id = str(uuid.uuid4())
            
            # Verificar que el usuario existe
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise ValueError(f"Usuario con ID {user_id} no encontrado")
            
            new_session = ChatSession(
                user_id=user_id,
                thread_id=thread_id
            )
            
            db.add(new_session)
            db.commit()
            db.refresh(new_session)
            
            logger.info(f"✅ Nueva sesión creada: {thread_id} para usuario {user_id}")
            return new_session
                
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error creando sesión para usuario {user_id}: {e}")
            raise
        finally:
            db.close()

    def get_user_sessions(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtiene las sesiones de un usuario"""
        db = SessionLocal()
        try:
            sessions = (
                db.query(ChatSession)
                .filter(ChatSession.user_id == user_id, ChatSession.is_active == True)
                .order_by(ChatSession.updated_at.desc())
                .limit(limit)
                .all()
            )

            logger.debug(f"✅ Sesiones obtenidas para usuario {user_id}: {len(sessions)} sesiones")
            return [
                {
                    "id": str(session.id),
                    "user_id": str(session.user_id),
                    "thread_id": session.thread_id,
                    "title": session.title,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at,
                    "is_active": session.is_active,
                    "message_count": session.message_count,
                    "metadata": session.metadata
                }
                for session in sessions
            ]
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo sesiones del usuario {user_id}: {e}")
            raise
        finally:
            db.close()

    def get_session_by_thread_id(self, thread_id: str) -> Dict[str, Any]:
        """Obtiene una sesión por su thread_id"""
        db = SessionLocal()
        try:
            session = (
                db.query(ChatSession)
                .filter(ChatSession.thread_id == thread_id, ChatSession.is_active == True)
                .first()
            )
            
            if session:
                return {
                    "id": str(session.id),
                    "user_id": str(session.user_id),
                    "thread_id": session.thread_id,
                    "title": session.title,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at,
                    "is_active": session.is_active,
                    "message_count": session.message_count,
                    "metadata": session.metadata
                }
            else:
                raise ValueError(f"Sesión con thread_id {thread_id} no encontrada")
                    
        except Exception as e:
            logger.error(f"❌ Error obteniendo sesión por thread_id {thread_id}: {e}")
            raise
        finally:
            db.close()

    def update_session_activity(self, thread_id: str):
        """Actualiza la actividad de una sesión"""
        db = SessionLocal()
        try:
            session = db.query(ChatSession).filter(ChatSession.thread_id == thread_id).first()
            if session:
                session.increment_message_count()
                session.updated_at = func.now()
                db.commit()
                logger.debug(f"✅ Actividad actualizada para sesión {thread_id}")
            else:
                raise ValueError(f"Sesión con thread_id {thread_id} no encontrada")
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error actualizando actividad de sesión {thread_id}: {e}")
            raise
        finally:
            db.close()

    def set_session_title(self, thread_id: str, title: str):
        """Establece el título de una sesión"""
        db = SessionLocal()
        try:
            session = db.query(ChatSession).filter(ChatSession.thread_id == thread_id).first()
            if session:
                session.update_title(title)
                db.commit()
                logger.info(f"✅ Título actualizado para sesión {thread_id}: {title}")
            else:
                raise ValueError(f"Sesión con thread_id {thread_id} no encontrada")
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error actualizando título de sesión {thread_id}: {e}")
            raise
        finally:
            db.close()

    def delete_session(self, user_id: str, thread_id: str) -> bool:
        """Elimina una sesión específica de un usuario"""
        db = SessionLocal()
        try:
            session = (
                db.query(ChatSession)
                .filter(ChatSession.user_id == user_id, ChatSession.thread_id == thread_id)
                .first()
            )
            
            if not session:
                return False
            
            # Marcar sesión como inactiva (soft delete)
            session.deactivate()
            db.commit()
            
            logger.info(f"✅ Sesión {thread_id} eliminada para usuario {user_id}")
            return True
                
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error eliminando sesión {thread_id}: {e}")
            raise
        finally:
            db.close()

    def auto_generate_title(self, thread_id: str, messages: list):
        """Genera automáticamente un título basado en el primer mensaje"""
        db = SessionLocal()
        try:
            session = db.query(ChatSession).filter(ChatSession.thread_id == thread_id).first()
            
            if session and session.message_count == 1 and session.title == "Nueva conversación":
                for msg in messages:
                    if hasattr(msg, 'content') and msg.__class__.__name__ == "HumanMessage":
                        title = msg.content[:50]
                        if len(msg.content) > 50:
                            title += "..."
                        session.update_title(title)
                        db.commit()
                        break
                            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error generando título automático: {e}")
        finally:
            db.close()

    def get_all_active_sessions(self, limit: int = 100) -> List[str]:
        """Obtiene todos los thread_id de las sesiones activas"""
        db = SessionLocal()
        try:
            sessions = (
                db.query(ChatSession.thread_id)
                .filter(ChatSession.is_active == True)
                .order_by(ChatSession.updated_at.desc())
                .limit(limit)
                .all()
            )
            return [session.thread_id for session in sessions]
        except Exception as e:
            logger.error(f"❌ Error obteniendo sesiones activas: {e}")
            return []
        finally:
            db.close()

    def get_session_stats(self, user_id: str) -> Dict[str, Any]:
        """Obtiene estadísticas de las sesiones de un usuario"""
        db = SessionLocal()
        try:
            total_sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id).count()
            active_sessions = db.query(ChatSession).filter(
                ChatSession.user_id == user_id, 
                ChatSession.is_active == True
            ).count()
            total_messages = db.query(func.sum(ChatSession.message_count)).filter(
                ChatSession.user_id == user_id
            ).scalar() or 0
            
            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "total_messages": total_messages
            }
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas del usuario {user_id}: {e}")
            raise
        finally:
            db.close()

# Instancia global del servicio
session_service = SessionService()