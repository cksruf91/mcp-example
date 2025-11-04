from fastapi import APIRouter

from agent import PlanAndExecuteChatService, PlanAndExecuteChattingRequest, ChatResponse

pne_router = APIRouter(prefix='/pne', tags=['pne'])


@pne_router.post('/complete')
async def get_chatting_message(request: PlanAndExecuteChattingRequest) -> ChatResponse:
    output = await PlanAndExecuteChatService(request).complete()
    return ChatResponse(roomId=request.roomId, message=output)

# @pne_router.post('/stream')
# async def get_chatting_message_in_stream(request: PlanAndExecuteChattingRequest) -> StreamingResponse:
#     return StreamingResponse(
#         PlanAndExecuteChatService(request).stream(),
#         media_type="text/event-stream"
#     )
