import sys
from fastapi import APIRouter, HTTPException
from shared.models import RegisterRequest, SendRequest, MessageResponse
from server.database import USERS, MESSAGES
from fastapi import WebSocket

router = APIRouter()

# Track connected clients
connected_clients: dict[str, WebSocket] = {}


@router.post("/register")
def register_user(req: RegisterRequest):
    if req.username in USERS:
        raise HTTPException(status_code=400, detail="Username already exists")
    if not req.kem_pk or not req.sig_pk:
        raise HTTPException(status_code=400, detail="Public keys cannot be empty")
    if not req.username:
        raise HTTPException(status_code=400, detail="Username cannot be empty")

    print("[SERVER] Registering user:", req.username, file=sys.stderr)

    # Store the user's public keys & init inbox
    USERS[req.username] = (req.kem_pk, req.sig_pk)
    MESSAGES[req.username] = []

    print(f"[SERVER] User '{req.username}' registered successfully.", file=sys.stderr)

    # Notify via WebSocket if connected
    return {"status": "registered"}


# TODO response model for public key
@router.get("/pubkey/{username}")
def get_public_key(username: str):
    if username not in USERS:
        raise HTTPException(status_code=404, detail="User not found")
    if not USERS[username][0] or not USERS[username][1]:
        raise HTTPException(status_code=404, detail="Public keys not found")

    print(f"[SERVER] Fetching public key for user: {username}", file=sys.stderr)

    # Return the user's public key and signature public key
    return {
        "username": username,
        "kem_pk": USERS[username][0],
        "sig_pk": USERS[username][1],
    }


@router.post("/send")
async def send_message(req: SendRequest):
    if req.recipient not in USERS:
        raise HTTPException(status_code=404, detail="Recipient not found")

    # Store the message in the recipient's inbox
    MESSAGES[req.recipient].append(
        {
            "sender": req.sender,
            "ciphertext": req.ciphertext,
            "nonce": req.nonce,
            "encapsulated_key": req.encapsulated_key,
            "signature": req.signature,
        }
    )

    # Notify via WebSocket if connected
    ws = connected_clients.get(req.recipient)
    if ws:
        try:
            await ws.send_text("new_message")
        except Exception as e:
            print(f"[WebSocket] Failed to notify {req.recipient}: {e}")

    return {"status": "message stored"}


@router.get("/inbox/{username}", response_model=list[MessageResponse])
def get_inbox(username: str):
    if username not in MESSAGES:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch the user's inbox messages & return them
    inbox = MESSAGES[username]

    # Clear inbox after retrieval TODO fix later
    MESSAGES[username] = []
    return inbox
