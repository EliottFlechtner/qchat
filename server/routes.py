import sys
from fastapi import APIRouter, HTTPException, Depends, WebSocket
from sqlalchemy.orm import Session
from server.db.database import get_db
from server.db.db_models import User, Message
from shared.requests_models import (
    RegisterRequest,
    SendRequest,
)
from shared.response_models import (
    RegisterResponse,
    GetPublicKeysResponse,
    SendResponse,
    MessageResponse,
)

router = APIRouter()

# Track connected clients
connected_clients: dict[str, WebSocket] = {}


@router.post("/register", response_model=RegisterResponse)
def register_user(req: RegisterRequest, db: Session = Depends(get_db)):
    if not req.username or not req.kem_pk or not req.sig_pk:
        raise HTTPException(status_code=400, detail="Missing required fields")

    existing_user = db.query(User).filter_by(username=req.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    print("[SERVER] Registering user:", req.username, file=sys.stderr)

    new_user = User(username=req.username, kem_pk=req.kem_pk, sig_pk=req.sig_pk)
    db.add(new_user)
    db.commit()

    print(f"[SERVER] User '{req.username}' registered successfully.", file=sys.stderr)
    return RegisterResponse(status="registered")


@router.get("/pubkey/{username}", response_model=GetPublicKeysResponse)
def get_public_key(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(username=username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    print(f"[SERVER] Fetching public key for user: {username}", file=sys.stderr)

    return GetPublicKeysResponse(
        username=user.username,
        kem_pk=user.kem_pk,
        sig_pk=user.sig_pk,
    )


@router.post("/send", response_model=SendResponse)
async def send_message(req: SendRequest, db: Session = Depends(get_db)):
    recipient = db.query(User).filter_by(username=req.recipient).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    new_message = Message(
        sender=req.sender,
        receiver=req.recipient,
        ciphertext=req.ciphertext,
        nonce=req.nonce,
        encapsulated_key=req.encapsulated_key,
        signature=req.signature,
    )
    db.add(new_message)
    db.commit()

    ws = connected_clients.get(req.recipient)
    if ws:
        try:
            await ws.send_text("new_message")
        except Exception as e:
            print(f"[WebSocket] Failed to notify {req.recipient}: {e}")

    return SendResponse(status="sent")


@router.get("/inbox/{username}", response_model=list[MessageResponse])
def get_inbox(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(username=username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    messages = db.query(Message).filter_by(receiver=username).all()

    # Convert to response model
    response = [
        MessageResponse(
            sender=m.sender,
            ciphertext=m.ciphertext,
            nonce=m.nonce,
            encapsulated_key=m.encapsulated_key,
            signature=m.signature,
        )
        for m in messages
    ]

    # Clear inbox (delete messages)
    for msg in messages:
        db.delete(msg)
    db.commit()

    return response
