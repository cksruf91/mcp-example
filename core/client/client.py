from fastapi import FastAPI

from route import ROUTES


def main():
    app = FastAPI(
        title="MCP Client",
        description="MCP Client",
        version="1.0"
    )

    for router in ROUTES:
        app.include_router(router)

    @app.get('/ping')
    async def ping():
        return {"ping": "Success"}

    return app
