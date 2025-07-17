from sqlalchemy import create_engine, update
from src.core.config import settings
from src.models import Base, User, ChatSession
from sqlalchemy.orm import sessionmaker

engine = create_engine(settings.POSTGRES_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def initialize_database():
    """
    Initializes the database by creating all tables defined in the models.
    """
    try:
        Base.metadata.create_all(bind=engine)
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

def get_db():
    """
    Returns a new database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()