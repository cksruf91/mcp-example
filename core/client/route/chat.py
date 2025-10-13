from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from models.request import ChattingRequest
from models.response import ChatResponse
from service.chat import ChatService

chat_router = APIRouter(prefix='/chat', tags=['chat'])


@chat_router.post('/main/complete')
async def get_chatting_message(request: ChattingRequest) -> ChatResponse:
    output = await ChatService(request).complete()
    return ChatResponse(roomId=request.roomId, message=output)


@chat_router.post('/main/stream')
async def get_chatting_message_in_stream(request: ChattingRequest) -> StreamingResponse:
    return StreamingResponse(
        ChatService(request).stream(),
        media_type="text/event-stream"
    )

