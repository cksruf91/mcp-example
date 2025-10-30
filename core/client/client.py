from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from route import ROUTES


def main():
    app = FastAPI(
        title="MCP Client",
        description="MCP Client",
        version="1.0"
    )

    # CORS 설정 - 프론트엔드 앱에서 API 호출 허용
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 개발 환경용, 프로덕션에서는 특정 도메인 지정
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for router in ROUTES:
        app.include_router(router)

    @app.get('/ping')
    async def ping():
        return {"ping": "Success"}

    # 정적 파일 서빙 (app.js 등)
    static_file_path = Path("resource/app")
    app.mount("/static", StaticFiles(directory=static_file_path), name="static")

    # 루트 경로에서 index.html 제공
    @app.get("/")
    async def serve_frontend():
        return FileResponse(static_file_path.joinpath("index.html"))

    return app
