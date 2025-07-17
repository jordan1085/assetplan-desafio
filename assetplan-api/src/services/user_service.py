from typing import Dict, Any
from src.models.user import User
from src.core.logging import logger
from src.database.postgres_config import SessionLocal

class UserService:
    """Servicio para manejar operaciones de usuarios usando SQLAlchemy"""
    def __init__(self):
        pass

    def create_or_get_user(
        self,
        email: str = None,
        username: str = None,
    ) -> Dict[str, Any]:
        """Crea un usuario o lo obtiene si ya existe"""
        db = SessionLocal()
        try:
            # Buscar usuario existente
            new_user = User(
                email=email,
                username=username,
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            return new_user
            
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()
            
    def get_all_users(self, limit: int = 100) -> list:
        """Obtiene todos los usuarios"""
        db = SessionLocal()
        try:
            users = db.query(User).order_by(User.created_at.desc()).limit(limit).all()
            return [
                {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email
                }
                for user in users
            ]
        except Exception as e:
            logger.error(f"❌ Error obteniendo todos los usuarios: {e}")
            raise
        finally:
            db.close()

user_service = UserService()