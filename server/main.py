from fastapi import FastAPI, WebSocket
from contextlib import asynccontextmanager
import asyncio

from server.db.database import engine, Base
from server.db.database_models import User, Message  # Safety import for Base
from server.routes import router, connected_clients
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


# Create FastAPI app and include the router
app = FastAPI(title="Post-Quantum Chat Server", lifespan=lifespan)
app.include_router(router)


# WebSocket endpoint watching & notifying for client connections
@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str) -> None:
    await websocket.accept()
    connected_clients[username] = websocket
    logger.debug(f"[WEBSOCKET] {username} connected.")

    try:
        while True:
            await websocket.receive_text()  # Just keep alive; client doesn't need to send.
    except Exception as e:
        logger.debug(f"[WEBSOCKET] {username} disconnected: {e}")
    finally:
        connected_clients.pop(username, None)
