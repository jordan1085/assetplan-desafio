from sqlalchemy import Column, String, DateTime, func, Integer
from sqlalchemy.orm import relationship
from . import Base

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    username = Column(String(200), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    chat_sessions = relationship("ChatSession", back_populates="user")