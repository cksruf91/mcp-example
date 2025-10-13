from .test import test_router
from .chat import chat_router
from .tool import tool_router

ROUTES = [
    tool_router,
    chat_router,
    test_router,
]
