# Initialize models package and expose models
from .favorites import Favorite
from .users import User
from .reviews import Review

__all__ = ["Favorite", "User", "Review"]