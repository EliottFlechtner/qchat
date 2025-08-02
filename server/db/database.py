import os, sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.exc import OperationalError

from server.utils.logger import logger


# Load environment variables for database configuration from .env file
load_dotenv()
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_NAME = os.getenv("POSTGRES_DB")
DB_PORT = os.getenv("POSTGRES_PORT", 5432)

# Ensure all required environment variables are set
if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_NAME]):
    logger.error(
        "[DATABASE] Missing required environment variables for database connection."
    )
    sys.exit(1)

# Define the postgreSQL connection URL with environment variables
SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
logger.info(f"[DATABASE] Connecting to {SQLALCHEMY_DATABASE_URL}")


# Check if the database is reachable
try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
except OperationalError as e:
    logger.error(f"[DATABASE] Could not connect to the database: {e}")
    sys.exit(1)

logger.info("[DATABASE] Database connection established successfully.")

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
