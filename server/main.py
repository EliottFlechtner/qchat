from fastapi import FastAPI, WebSocket
from server.routes import router, connected_clients
from shared.models import RegisterRequest

app = FastAPI(title="Post-Quantum Chat Server")
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
