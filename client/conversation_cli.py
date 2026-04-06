"""
Conversation CLI for the qchat client.

Provides commands for managing conversations including listing conversations,
viewing conversation messages, and starting new conversations.
"""

import sys

from client.services.login import login_or_register, get_local_keypair
from client.services.conversation import (
    fetch_user_conversations,
    fetch_conversation_messages,
    get_or_create_conversation_id,
)
from client.services.send import send_encrypted_message
from client.api import get_public_key


def list_conversations(username: str) -> None:
    """List all conversations for a user.

    :param username: Username whose conversations to list.
    """
    try:
        conversations = fetch_user_conversations(username)

        if not conversations:
            print("No conversations found.")
            return

        print(f"\n{username}'s Conversations:")
        print("-" * 50)

        for i, conv in enumerate(conversations, 1):
            other_user = conv["other_user"]
            created_at = conv["created_at"]
            updated_at = conv["updated_at"]

            print(f"{i}. {other_user}")
            print(f"   Created: {created_at}")
            print(f"   Updated: {updated_at}")
            print(f"   ID: {conv['id']}")
            print()

    except Exception as e:
        print(f"Error listing conversations: {e}", file=sys.stderr)


def view_conversation(username: str, other_user: str, decrypt: bool = True) -> None:
    """View messages in a conversation with another user.

    :param username: Current user's username.
    :param other_user: Other user's username.
    :param decrypt: Whether to decrypt messages (requires local keys).
    """
    try:
        # Find the conversation ID
        conversation_id = get_or_create_conversation_id(username, other_user)

        if not conversation_id:
            print(f"No conversation found between {username} and {other_user}")
            return

        print(f"\nConversation between {username} and {other_user}:")
        print("-" * 60)

        # Get user's keys for decryption if requested
        kem_sk = None
        sig_pk_cache = {}

        if decrypt:
            try:
                # Get local keys for decryption
                kem_pk, kem_sk = get_local_keypair(username, "kem")

                # Get other user's signature public key for verification
                other_sig_pk = get_public_key(other_user, "sig_pk")
                sig_pk_cache[other_user] = other_sig_pk

            except Exception as e:
                print(
                    f"Warning: Could not load keys for decryption: {e}", file=sys.stderr
                )
                decrypt = False

        # Fetch messages
        messages = fetch_conversation_messages(
            username,
            conversation_id,
            decrypt=decrypt,
            kem_sk=kem_sk,
            sig_pk_cache=sig_pk_cache,
        )

        if not messages:
            print("No messages in this conversation.")
            return

        # Display messages
        for msg in messages:
            sender = msg["sender"]
            sent_at = msg["sent_at"]

            if decrypt and "content" in msg:
                content = msg["content"]
                verified = msg.get("signature_verified", False)
                verify_status = "✓" if verified else "?"
                print(f"[{sent_at}] {sender} {verify_status}: {content}")
            else:
                # Show encrypted message info
                print(f"[{sent_at}] {sender}: [ENCRYPTED MESSAGE]")

    except Exception as e:
        print(f"Error viewing conversation: {e}", file=sys.stderr)


def interactive_conversation_menu(username: str) -> None:
    """Interactive menu for conversation operations.

    :param username: Current user's username.
    """
    print(f"\nConversation Menu for {username}")
    print("=" * 40)

    while True:
        print("\nOptions:")
        print("1. List all conversations")
        print("2. View conversation with user")
        print("3. Send message to user")
        print("4. Exit")

        try:
            choice = input("\nEnter your choice (1-4): ").strip()

            if choice == "1":
                list_conversations(username)

            elif choice == "2":
                other_user = input("Enter username to view conversation with: ").strip()
                if other_user:
                    decrypt_choice = input("Decrypt messages? (y/n): ").strip().lower()
                    decrypt = decrypt_choice in ["y", "yes"]
                    view_conversation(username, other_user, decrypt)
                else:
                    print("Username cannot be empty.")

            elif choice == "3":
                other_user = input("Enter recipient username: ").strip()
                message = input("Enter message: ").strip()
                if other_user and message:
                    try:
                        send_encrypted_message(username, other_user, message)
                        print("Message sent successfully!")
                    except Exception as e:
                        print(f"Error sending message: {e}")
                else:
                    print("Username and message cannot be empty.")

            elif choice == "4":
                print("Goodbye!")
                break

            else:
                print("Invalid choice. Please enter 1-4.")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break


def main() -> None:
    """Main conversation CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python -m client.conversation_cli <username> [command] [args...]")
        print("\nCommands:")
        print("  list                    - List all conversations")
        print("  view <other_user>       - View conversation with another user")
        print("  send <other_user> <msg> - Send a message to another user")
        print("  menu                    - Interactive menu")
        print("\nIf no command is provided, interactive menu is used.")
        sys.exit(1)

    username = sys.argv[1].strip()
    if not username:
        print("Username cannot be empty.")
        sys.exit(1)

    print(f"[Conversation CLI] Initializing for user: {username}")

    # Register/login the user
    try:
        login_or_register(username)
    except Exception as e:
        print(f"Error during login/registration: {e}", file=sys.stderr)
        sys.exit(1)

    # Parse command
    if len(sys.argv) == 2:
        # No command provided, use interactive menu
        interactive_conversation_menu(username)
    elif len(sys.argv) >= 3:
        command = sys.argv[2].lower()

        if command == "list":
            list_conversations(username)

        elif command == "view" and len(sys.argv) >= 4:
            other_user = sys.argv[3].strip()
            view_conversation(username, other_user)

        elif command == "send" and len(sys.argv) >= 5:
            other_user = sys.argv[3].strip()
            message = " ".join(sys.argv[4:])
            try:
                send_encrypted_message(username, other_user, message)
                print("Message sent successfully!")
            except Exception as e:
                print(f"Error sending message: {e}")

        elif command == "menu":
            interactive_conversation_menu(username)

        else:
            print(f"Unknown command: {command}")
            print("Use 'python -m client.conversation_cli <username>' for help.")
            sys.exit(1)


if __name__ == "__main__":
    main()
