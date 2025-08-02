from pydantic import BaseModel


class RegisterResponse(BaseModel):
    status: str


class SendResponse(BaseModel):
    status: str


class GetPublicKeysResponse(BaseModel):
    username: str
    kem_pk: str  # base64 encoded
    sig_pk: str  # base64 encoded


class MessageResponse(BaseModel):
    sender: str
    ciphertext: str  # base64 encoded
    nonce: str  # base64 encoded
    encapsulated_key: str  # base64 encoded
    signature: str  # base64 encoded
