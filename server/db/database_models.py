from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from server.db.database import Base  # import the shared Base from database.py


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False
    )
    kem_pk: Mapped[str] = mapped_column(Text, nullable=False)
    sig_pk: Mapped[str] = mapped_column(Text, nullable=False)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    sender: Mapped[str] = mapped_column(Text, nullable=False)
    receiver: Mapped[str] = mapped_column(Text, nullable=False)
    ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    nonce: Mapped[str] = mapped_column(Text, nullable=False)
    encapsulated_key: Mapped[str] = mapped_column(Text, nullable=False)
    signature: Mapped[str] = mapped_column(Text, nullable=False)
