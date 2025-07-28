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
    USERS[req.username] = req.public_key
    MESSAGES[req.username] = []
    return {"status": "registered"}


@router.post("/send")
async def send_message(req: SendRequest):
    if req.recipient not in USERS:
        raise HTTPException(status_code=404, detail="Recipient not found")
    MESSAGES[req.recipient].append(
        {
            "sender": req.sender,
            "ciphertext": req.ciphertext,
            "nonce": req.nonce,
            "encapsulated_key": req.encapsulated_key,
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
    inbox = MESSAGES[username]
    MESSAGES[username] = []  # Empty inbox after retrieval
    return inbox


@router.get("/pubkey/{username}")
def get_public_key(username: str):
    if username not in USERS:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": username, "public_key": USERS[username]}
