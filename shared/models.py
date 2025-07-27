from pydantic import BaseModel


class RegisterRequest(BaseModel):
    username: str
    public_key: str  # base64 encoded


class SendRequest(BaseModel):
    sender: str
    recipient: str
    ciphertext: str  # base64
    nonce: str  # base64
    encapsulated_key: str  # base64


class MessageResponse(BaseModel):
    sender: str
    ciphertext: str
    nonce: str
    encapsulated_key: str
