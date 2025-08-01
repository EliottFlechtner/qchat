from pydantic import BaseModel


class RegisterRequest(BaseModel):
    username: str
    kem_pk: str  # base64 encoded
    sig_pk: str  # base64 encoded


class SendRequest(BaseModel):
    sender: str
    recipient: str
    ciphertext: str  # base64
    nonce: str  # base64
    encapsulated_key: str  # base64
    signature: str  # base64


class MessageResponse(BaseModel):
    sender: str
    ciphertext: str  # base64 encoded
    nonce: str  # base64 encoded
    encapsulated_key: str  # base64 encoded
    signature: str  # base64 encoded
