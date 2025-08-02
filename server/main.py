from fastapi import FastAPI, WebSocket
from server.db.database import engine, Base, wait_for_db
from server.db.db_models import User, Message
from server.routes import router, connected_clients
from contextlib import asynccontextmanager
import logging, asyncio

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Lifespan startup: waiting for DB and creating tables")

    # Wait for DB synchronously (blocking call allowed here)
    wait_for_db(engine)

    # Run create_all synchronously but in a thread so it doesn't block event loop
    logger.info(Base.metadata.tables.keys())
    await asyncio.to_thread(Base.metadata.create_all, engine)
    logger.info("Lifespan startup: database ready, creating tables")

    yield

    logger.info("Lifespan shutdown: done")


# Create FastAPI app and include the router
app = FastAPI(title="Post-Quantum Chat Server", lifespan=lifespan)
app.include_router(router)


@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await websocket.accept()
    connected_clients[username] = websocket
    print(f"[WebSocket] {username} connected.")

    try:
        while True:
            await websocket.receive_text()  # Just keep alive; client doesn't need to send.
    except Exception as e:
        print(f"[WebSocket] {username} disconnected: {e}")
    finally:
        connected_clients.pop(username, None)
