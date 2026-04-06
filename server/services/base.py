"""Base service class providing common database session handling."""

from abc import ABC
from sqlalchemy.orm import Session


class BaseService(ABC):
    """Abstract base class for all services providing common functionality."""

    def __init__(self, db: Session):
        """Initialize service with database session.

        :param db: SQLAlchemy database session
        """
        self.db = db
