import asyncio, threading, websockets

from client.services.inbox import fetch_and_decrypt_inbox

API_WS_URL = "ws://localhost:8000/ws"


def start_ws_listener(username):
    async def listen():
        uri = f"{API_WS_URL}/{username}"
        try:
            async with websockets.connect(uri) as ws:
                while True:
                    await ws.recv()
                    fetch_and_decrypt_inbox(username)
        except Exception as e:
            print(f"[WS Error] {e}")

    asyncio.run(listen())


def start_websocket_thread(username):
    thread = threading.Thread(target=start_ws_listener, args=(username,), daemon=True)
    thread.start()
