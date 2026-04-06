import sys

from client.services.login import login_or_register
from client.services.send import send_encrypted_message
from client.network.websocket import start_websocket_thread


def show_help():
    """Show usage instructions."""
    print("Usage: python client/main.py <your_username> [recipient_username]")
    print("\nModes:")
    print("  python client/main.py <username> <recipient>   - Direct chat mode")
    print(
        "  python client/main.py <username>               - Conversation management mode"
    )
    print("\nFor conversation management, you can also use:")
    print("  python -m client.conversation_cli <username>")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)

    username = sys.argv[1]
    if not username:
        print("Username cannot be empty.")
        sys.exit(1)

    # Register the user if not already registered
    login_or_register(username)

    if len(sys.argv) == 3:
        # Direct chat mode with specific recipient
        recipient = sys.argv[2]
        if not recipient:
            print("Recipient username cannot be empty.")
            sys.exit(1)

        print(f"[Chat Client] Starting direct chat as '{username}' with '{recipient}'")

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

    else:
        # Conversation management mode
        print(f"[Chat Client] Starting conversation manager for '{username}'")
        print("Use the conversation CLI for full conversation management:")
        print(f"  python -m client.conversation_cli {username}")
        print("\nBasic conversation listing:")

        try:
            from client.services.conversation import fetch_user_conversations

            conversations = fetch_user_conversations(username)

            if not conversations:
                print("No conversations found.")
            else:
                print(f"\n{username}'s Conversations:")
                print("-" * 30)
                for i, conv in enumerate(conversations, 1):
                    print(f"{i}. {conv['other_user']} (ID: {conv['id'][:8]}...)")

        except Exception as e:
            print(f"Error listing conversations: {e}", file=sys.stderr)
