from .animes import router as animes_router
from .auth import router as auth_router
from .user_list import router as list_router
from .recommendations import router as recommendations
from .home import router as home_router

__all__ = [
    'animes_router',
    'auth_router',
    'list_router',
    'recommendations',
    'home_router',
]