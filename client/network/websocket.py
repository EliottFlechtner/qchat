import asyncio, threading, websockets

from client.services.inbox import fetch_and_decrypt_inbox

API_WS_URL = "ws://localhost:8000/ws"


def start_ws_listener(username: str) -> None:
    async def listen():
        uri = f"{API_WS_URL}/{username}"
        try:
            async with websockets.connect(uri) as ws:
                # Initially fetch pending inbox messages if any
                print("[WS] Connected to WebSocket. Fetching inbox messages...")
                await asyncio.to_thread(fetch_and_decrypt_inbox, username)

                print("[WS] Listening for new messages...")
                while True:
                    await ws.recv()  # Blocking call to wait for notifications

                    # Fetch and decrypt the inbox messages
                    print("[WS] New message received, fetching inbox...")
                    await asyncio.to_thread(fetch_and_decrypt_inbox, username)
        except websockets.ConnectionClosed as e:
            print(f"[WS] Connection closed: {e}")
        except websockets.InvalidURI as e:
            print(f"[WS] Invalid URI: {e}")
        except websockets.InvalidHandshake as e:
            print(f"[WS] Invalid handshake: {e}")
        except websockets.WebSocketException as e:
            print(f"[WS] WebSocket error: {e}")
        except KeyboardInterrupt:
            print("\n[WS] Listener interrupted. Exiting.")
        except Exception as e:
            print(f"[WS] Uncaught exception: {e}")

    asyncio.run(listen())


def start_websocket_thread(username: str) -> None:
    thread = threading.Thread(target=start_ws_listener, args=(username,), daemon=True)
    thread.start()
