from inbox import *
from send import *

if __name__ == "__main__":
    while True:
        username = input("Enter your username: ").strip()
        if username:
            break
        print("Username cannot be empty. Please try again.")
    register_local_user(username)

    while True:
        action = input("Choose an action (send/fetch/exit): ").strip().lower()
        if action == "send":
            recipient = input("Enter recipient username: ").strip()
            message = input("Enter your message: ").strip()
            send_encrypted_message(username, recipient, message)
        elif action == "fetch":
            fetch_and_decrypt_inbox(username)
        elif action == "exit":
            print("Exiting...")
            break
        else:
            print("Invalid action. Please choose 'send', 'fetch', or 'exit'.")
    print("Goodbye!")
