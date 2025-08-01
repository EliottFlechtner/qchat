import sys

from client.services.login import login_or_register
from client.services.send import send_encrypted_message
from client.network.websocket import start_websocket_thread

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python client_chat.py <your_username> <recipient_username>")
        sys.exit(1)

    username = sys.argv[1]
    if not username:
        print("Username cannot be empty.")
        sys.exit(1)

    recipient = sys.argv[2]
    if not recipient:
        print("Recipient username cannot be empty.")
        sys.exit(1)

    print(f"[Chat Client] Starting chat as '{username}' with '{recipient}'")

    # Register the user if not already registered
    login_or_register(username)

    # Start the WebSocket listener in a separate thread
    start_websocket_thread(username)

    print(
        f"[CLIENT] You are now connected as '{username}'. You can start sending messages to '{recipient}'.",
        file=sys.stderr,
    )
    print("Type your messages below (Ctrl+C to exit):")
    print("--------------------------------------------------")

    try:
        # Main loop to read user input and send messages
        while True:
            msg = input("> ").strip()
            if msg:
                send_encrypted_message(username, recipient, msg)
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
