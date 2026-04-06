import asyncio
import threading
import websockets
from typing import Optional

from client.services.inbox import fetch_and_decrypt_inbox
from client.utils.helpers import get_ws_url


def start_ws_listener(username: str) -> None:
    """Starts the WebSocket listener for real-time message notifications.

    This function establishes a persistent WebSocket connection to receive real-time
    notifications when new messages arrive. It runs in an asyncio event loop and
    handles connection management, error recovery, and message fetching.

    Connection workflow:
    1. Connect to WebSocket endpoint with username
    2. Fetch any pending inbox messages on initial connection
    3. Listen for incoming message notifications
    4. Fetch and decrypt new messages when notifications arrive
    5. Handle connection errors and reconnection attempts

    The WebSocket connection is used purely for notifications - the actual message
    data is fetched separately via HTTP API calls for security and reliability.

    :param username: The username to listen for messages (used in WebSocket URL).
    :raises TypeError: If username is not a string.
    :raises ValueError: If username is empty or invalid.
    """
    # Validate username parameter
    if not isinstance(username, str):
        raise TypeError("Username must be a string")
    if not username or not username.strip():
        raise ValueError("Username must be a non-empty string")

    async def listen() -> None:
        """Inner async function that handles the WebSocket connection and message listening."""
        # Construct WebSocket URI with the username for targeted notifications
        uri = f"{get_ws_url()}/{username.strip()}"

        try:
            # Establish WebSocket connection with automatic ping/pong handling
            async with websockets.connect(uri) as ws:
                print(f"[WS] Connected to WebSocket for user '{username}'")

                # Initially fetch any pending inbox messages that arrived while offline
                print("[WS] Fetching pending inbox messages...")
                try:
                    await asyncio.to_thread(fetch_and_decrypt_inbox, username)
                    print("[WS] Initial inbox fetch completed")
                except Exception as e:
                    print(f"[WS] Warning: Initial inbox fetch failed: {e}")

                print("[WS] Listening for new message notifications...")

                # Main listening loop - wait for server notifications
                while True:
                    try:
                        # Blocking call to wait for WebSocket notifications
                        # The server sends a notification when new messages arrive
                        notification = await ws.recv()
                        print(f"[WS] Received notification: {notification}")

                        # Fetch and decrypt the new inbox messages
                        print(
                            "[WS] New message notification received, fetching inbox..."
                        )
                        await asyncio.to_thread(fetch_and_decrypt_inbox, username)
                        print("[WS] Inbox fetch completed")

                    except websockets.ConnectionClosed:
                        print("[WS] Connection closed by server, will exit listener")
                        break
                    except Exception as e:
                        print(f"[WS] Error processing notification: {e}")
                        # Continue listening despite processing errors
                        continue

        except websockets.ConnectionClosed as e:
            print(f"[WS] WebSocket connection closed: {e}")
        except websockets.InvalidURI as e:
            print(f"[WS] Invalid WebSocket URI '{uri}': {e}")
        except websockets.InvalidHandshake as e:
            print(f"[WS] WebSocket handshake failed: {e}")
        except websockets.WebSocketException as e:
            print(f"[WS] WebSocket protocol error: {e}")
        except KeyboardInterrupt:
            print("\n[WS] WebSocket listener interrupted by user")
        except OSError as e:
            print(f"[WS] Network error: {e}")
        except Exception as e:
            print(f"[WS] Unexpected error in WebSocket listener: {e}")
        finally:
            print(f"[WS] WebSocket listener for '{username}' has stopped")

    # Run the async WebSocket listener in the current thread's event loop
    try:
        asyncio.run(listen())
    except Exception as e:
        print(f"[WS] Failed to start asyncio event loop: {e}")


def start_websocket_thread(username: str) -> threading.Thread:
    """Starts the WebSocket listener in a separate daemon thread.

    This function creates and starts a background thread that runs the WebSocket listener.
    Using a daemon thread ensures that the WebSocket listener will not prevent the main
    program from exiting when the user terminates the application.

    Thread characteristics:
    - Daemon thread: Automatically terminates when main program exits
    - Background operation: Does not block the main thread
    - Error isolation: WebSocket errors do not crash the main application
    - Real-time notifications: Enables immediate message delivery

    :param username: The username to listen for messages.
    :return: The created thread object (already started).
    :raises TypeError: If username is not a string.
    :raises ValueError: If username is empty or invalid.
    :raises RuntimeError: If thread creation fails.
    """
    # Validate username parameter (same validation as start_ws_listener)
    if not isinstance(username, str):
        raise TypeError("Username must be a string")
    if not username or not username.strip():
        raise ValueError("Username must be a non-empty string")

    try:
        # Create daemon thread for WebSocket listener
        # daemon=True ensures the thread exits when the main program exits
        thread = threading.Thread(
            target=start_ws_listener,
            args=(username,),
            daemon=True,
            name=f"WebSocket-{username}",  # Named thread for easier debugging
        )

        # Start the thread immediately
        thread.start()
        print(f"[WS] Started WebSocket listener thread for user '{username}'")

        # Return the thread object for potential monitoring or joining
        return thread

    except Exception as e:
        raise RuntimeError(f"Failed to start WebSocket thread for '{username}': {e}")
