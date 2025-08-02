import os
import sys
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_NAME = os.getenv("POSTGRES_DB")
DB_PORT = os.getenv("POSTGRES_PORT", 5432)

SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
print(f"[DATABASE] Connecting to {SQLALCHEMY_DATABASE_URL}", file=sys.stderr)

# Create the SQLAlchemy engine and session
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Function to wait for the database to be ready before starting the app
# Ensures case the app starts before the DB is ready DOES NOT happen
def wait_for_db(engine, retries=10, delay=2):
    for _ in range(retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("[DATABASE] Database is ready!")
            return
        except OperationalError:
            print("[DATABASE] Waiting for database to be ready...")
            time.sleep(delay)
    raise Exception("[DATABASE] Could not connect to the database.")
