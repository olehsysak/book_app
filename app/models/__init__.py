# Initialize models package and expose models
from .favorites import Favorite
from .users import User

__all__ = ["Favorite", "User"]