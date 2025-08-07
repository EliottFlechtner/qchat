from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio

from server.db.database import engine, Base
from server.db.database_models import User, Message  # Safety import for Base
from server.routes.http_routes import router
from server.routes.ws_routes import ws_router as ws_router
from server.utils.logger import logger
from server.config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run create_all synchronously but in a thread so it doesn't block event loop
    logger.debug("[DATABASE] DB ready, creating tables")
    await asyncio.to_thread(Base.metadata.create_all, engine)
    logger.debug("[DATABASE] Tables created")

    # Log configuration on startup
    logger.info(
        f"[CONFIG] Server starting with KEM: {settings.kem_algorithm}, SIG: {settings.sig_algorithm}"
    )
    logger.info(
        f"[CONFIG] Database: {settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
    )
    logger.info(f"[CONFIG] Debug mode: {settings.debug}")

    # Yield control back to the app
    yield

    # Cleanup on shutdown
    logger.debug("[DATABASE] Shutting down database connection")


# Create FastAPI app and include routers
app = FastAPI(
    title="QChat - Post-Quantum Chat Server",
    description="A secure chat server using post-quantum cryptography",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan,
)
app.include_router(router)
app.include_router(ws_router, prefix="/ws", tags=["WebSocket"])
