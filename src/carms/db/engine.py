"""
Database engine configuration and session management.
"""
from sqlmodel import create_engine, Session
from src.carms.config import settings

# Create the SQLAlchemy engine using the configured database URL
engine = create_engine(settings.DATABASE_URL, echo=False)

def get_session():
    """
    Dependency for FastAPI endpoints to provide a database session.
    Yields a Session object and ensures it is closed after use.
    """
    with Session(engine) as session:
        yield session
