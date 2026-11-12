"""Repositories Package.

Encapsulates data access and persistence logic on top of SQLAlchemy 2.0 AsyncSession.
"""

from app.repositories.base import BaseRepository
from app.repositories.room_repository import RoomRepository
from app.repositories.user_repository import UserRepository
from app.repositories.wallet_repository import WalletRepository

__all__ = [
    "BaseRepository",
    "RoomRepository",
    "UserRepository",
    "WalletRepository",
]
