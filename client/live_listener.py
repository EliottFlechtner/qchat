import asyncio
import websockets
from inbox import fetch_and_decrypt_inbox

API_WS = "ws://localhost:8000/ws"


async def listen(username: str):
    async with websockets.connect(f"{API_WS}/{username}") as websocket:
        print(f"[WebSocket] Connected as {username}")
        while True:
            msg = await websocket.recv()
            print(f"[WebSocket] Notification received: {msg}")
            fetch_and_decrypt_inbox(username)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python live_listener.py <username>")
        exit()
    asyncio.run(listen(sys.argv[1]))
