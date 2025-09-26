from fastapi import APIRouter

from models.request import ChattingRequest
from models.response import ChatResponse
from service.chat import ChatService

chat_router = APIRouter(prefix='/chat', tags=['chat'])


@chat_router.post('/main')
async def get_chatting_message(request: ChattingRequest) -> ChatResponse:
    service = ChatService(request)
    return await service.run()
