import uuid
from sqlalchemy import ForeignKey, Integer, String, Text, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from server.db.database import Base  # import the shared Base from database.py


class User(Base):
    __tablename__ = "users"

    # Identifiers
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    kem_pk: Mapped[str] = mapped_column(Text, nullable=False)
    sig_pk: Mapped[str] = mapped_column(Text, nullable=False)

    # Timestamps
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Message(Base):
    __tablename__ = "messages"

    # Identifiers (ids & type)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    recipient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    type: Mapped[str] = mapped_column(String, nullable=False)  # e.g, "text", "file"

    # Status flags
    sent: Mapped[bool] = mapped_column(Boolean, default=False)
    delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    read: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    sent_timestamp: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    delivered_timestamp: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    read_timestamp: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Encryption metadata
    ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    nonce: Mapped[str] = mapped_column(Text, nullable=False)
    encapsulated_key: Mapped[str] = mapped_column(Text, nullable=False)
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    def __repr__(self):
        return (
            f"<Message(id={self.id}, sender_id={self.sender_id}, recipient_id={self.recipient_id}, "
            f"sent={self.sent}, delivered={self.delivered}, read={self.read})>"
        )
