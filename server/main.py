from fastapi import FastAPI, WebSocket
from contextlib import asynccontextmanager
import asyncio

from server.db.database import engine, Base
from server.db.database_models import User, Message  # Safety import for Base
from server.routes.http_routes import router
from server.routes.ws_routes import ws_router as ws_router
from server.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run create_all synchronously but in a thread so it doesn't block event loop
    logger.debug("[DATABASE] DB ready, creating tables")
    await asyncio.to_thread(Base.metadata.create_all, engine)
    logger.debug("[DATABASE] Tables created")

    # Yield control back to the app
    yield

    # Cleanup on shutdown
    logger.debug("[DATABASE] Shutting down database connection")


# Create FastAPI app and include routers
app = FastAPI(title="Post-Quantum Chat Server", lifespan=lifespan)
app.include_router(router)
app.include_router(ws_router, prefix="/ws", tags=["WebSocket"])
