from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from server.utils.logger import logger
from server.config.settings import settings


# Get database URL from centralized configuration
SQLALCHEMY_DATABASE_URL = settings.database_url
logger.info(
    f"[DATABASE] Connecting to database at {settings.postgres_host}:{settings.postgres_port}"
)

# Engine creation does not open a connection immediately. This avoids import-time
# failures in environments where the database is not available (e.g. unit tests).
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create the SQLAlchemy engine and session
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


# Base class for declarative models, shared across the application to ensure consistency
# see server/db/database_models.py for model definitions inheriting from this Base
class Base(DeclarativeBase):
    pass


# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db  # Yield the session to be used in routes
    finally:
        db.close()  # Ensure the session is closed after use
