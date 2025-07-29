import asyncio
import threading
import sys
import websockets
from inbox import fetch_and_decrypt_inbox, register_local_user
from send import send_encrypted_message

from client_helpers import *

API_WS_URL = "ws://localhost:8000/ws"


def start_ws_listener(username):
    async def listen():
        uri = f"{API_WS_URL}/{username}"
        # print(f"[WS] Connecting to {uri}...")
        try:
            async with websockets.connect(uri) as ws:
                # print(f"[WS] Listening for messages for {username}...")
                while True:
                    msg = await ws.recv()
                    # print("\n🔔 New message received!")
                    fetch_and_decrypt_inbox(username)
        except Exception as e:
            print(f"[WS Error] {e}")

    asyncio.run(listen())


def start_websocket_thread(username):
    thread = threading.Thread(target=start_ws_listener, args=(username,), daemon=True)
    thread.start()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python client_chat.py <your_username> <recipient_username>")
        sys.exit(1)

    username = sys.argv[1]
    recipient = sys.argv[2]

    register_local_user(username)
    start_websocket_thread(username)

    print(f"[Chat Started] You are '{username}', chatting with '{recipient}'")
    print("Type your message and press Enter. Type EXIT() to quit.")

    try:
        while True:
            msg = input("> ").strip()
            if msg == "EXIT()":
                print("Exiting chat...")
                break
            if msg:
                send_encrypted_message(username, recipient, msg)
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
