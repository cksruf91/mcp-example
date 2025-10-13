from .auth import auth_router
from .chat import chat_router
from .tool import tool_router

ROUTES = [
    auth_router,
    tool_router,
    chat_router,
]
