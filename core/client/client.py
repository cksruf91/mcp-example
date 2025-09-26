from fastapi import FastAPI

from route.chat import chat_router
from route.tool import tool_router


def main():
    app = FastAPI(
        title="MCP Client",
        description="MCP Client",
        version="1.0"
    )

    app.include_router(tool_router)
    app.include_router(chat_router)

    @app.get('/ping')
    async def ping():
        return {"ping": "Success"}

    return app
