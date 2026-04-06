from pydantic import BaseModel
from datetime import datetime
from typing import List
import uuid


class RegisterResponse(BaseModel):
    status: str


class SendResponse(BaseModel):
    status: str


class GetPublicKeysResponse(BaseModel):
    username: str
    kem_pk: str  # base64 encoded
    sig_pk: str  # base64 encoded


class MessageResponse(BaseModel):
    sender: str  # username of the sender
    ciphertext: str  # base64 encoded
    nonce: str  # base64 encoded
    encapsulated_key: str  # base64 encoded
    signature: str  # base64 encoded
    sent_at: datetime  # ISO 8601 formatted string


class ConversationResponse(BaseModel):
    id: str  # UUID as string
    other_user: str  # username of the other user in the conversation
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(BaseModel):
    conversations: List[ConversationResponse]


class ConversationMessagesResponse(BaseModel):
    conversation_id: str  # UUID as string
    messages: List[MessageResponse]
