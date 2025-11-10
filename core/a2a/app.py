import uuid
from pathlib import Path
from typing import Any
from typing import Literal
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    MessageSendParams,
    SendMessageRequest,
    SendMessageResponse,
)
from fastapi import APIRouter
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from a2a.types import Message as A2aMessage
from pydantic import BaseModel, Field

pne_router = APIRouter(prefix='/pne', tags=['pne'])


class PlanAndExecuteChattingRequest(BaseModel):
    question: str = Field(
        default="안녕?"
    )
    roomId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    history: list[tuple[Literal['user', 'assistant'], str]] = Field(
        default_factory=lambda: [],
        description="chat history, format: [(\"user\",\"hello\"), (\"assistant\": \"hi! how are you doing?\nhow can i help you?\")]"
    )


class ChatResponse(BaseModel):
    message: str = Field()
    roomId: str = Field()


@pne_router.post('/complete')
async def get_chatting_message(request: PlanAndExecuteChattingRequest) -> ChatResponse:
    async with httpx.AsyncClient() as httpx_client:
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url='http://localhost:9999',
            # agent_card_path uses default, extended_agent_card_path also uses default
        )
        public_agent_card = await resolver.get_agent_card()
        if public_agent_card.supports_authenticated_extended_card:
            ...  # pass
        client = A2AClient(
            httpx_client=httpx_client, agent_card=public_agent_card
        )

        send_message_payload: dict[str, Any] = {
            'message': {
                'role': 'user',
                'parts': [
                    {'kind': 'text', 'text': request.question},
                ],
                'messageId': uuid4().hex,
            },
        }
        message_request = SendMessageRequest(
            id=str(uuid4()), params=MessageSendParams(**send_message_payload)
        )
        response: SendMessageResponse = await client.send_message(message_request)
        output_json = response.model_dump(mode='json', exclude_none=True)

    # custom
    return ChatResponse(roomId=request.roomId, message=output_json['result']['parts'][0]['text'])


def main():
    app = FastAPI(
        title="A2A Protocol Repeater",
        description="A2A Protocol Repeater",
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

    app.include_router(pne_router)

    # 정적 파일 서빙 (app.js 등)
    static_file_path = Path("resource/app")
    app.mount("/static", StaticFiles(directory=static_file_path), name="static")

    # 루트 경로에서 index.html 제공
    @app.get("/")
    async def serve_frontend():
        return FileResponse(static_file_path.joinpath("index.html"))

    return app
