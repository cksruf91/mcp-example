from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from models.request import PlanAndExecuteChattingRequest
from models.response import ChatResponse
from service.pne import PlanAndExecuteChatService

pne_router = APIRouter(prefix='/pne', tags=['pne'])


@pne_router.post('/complete')
async def get_chatting_message(request: PlanAndExecuteChattingRequest) -> ChatResponse:
    output = await PlanAndExecuteChatService(request).complete()
    return ChatResponse(roomId=request.roomId, message=output)


@pne_router.post('/stream')
async def get_chatting_message_in_stream(request: PlanAndExecuteChattingRequest) -> StreamingResponse:
    async def fake_stream():
        text = """
        this is first line
        and second line
        and third line
        and fourth line
        and fifth line
        and sixth line
        and seven line
        and eight line
        and nine line
        final line
        """
        async for line in text:
            yield line

    return StreamingResponse(
        fake_stream(),
        media_type="text/event-stream"
    )
