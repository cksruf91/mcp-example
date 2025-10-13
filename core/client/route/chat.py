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


@chat_router.get('/test/stream')
async def get_chatting_message_in_stream() -> StreamingResponse:
    async def fake_stream():
        import asyncio
        data = """
if you hold a gun and I hold a gun, we can talk about the law.
If you hold a knife and I hold a knife, we can talk about rules.
If you come empty handed and I come empty handed, we can talk about reason.
But if you have a gun and I only have a knife, then the truth lies in your hands.
If you have a gun and I have nothing, what you hold isn't just a weapon, it's my life.
The concepts of laws, rules and morality only hold meaning when they are based on equality.
The harsh truth of this world is that when money speaks, truth goes silent. And when power speaks, even money takes three steps back.
Those who create the rules are often the first to break them. Rules are chains for the weak, tools for the strong.
In this world, anything good must be fought for.
The masters of the game are fiercely competing for resources while only the weak sit idly, waiting to be given a share.
"""
        buffer = []
        for char in data:
            await asyncio.sleep(0.01)
            if char == '\n':
                print(''.join(buffer))
                buffer = []
            else:
                buffer.append(char)
            yield char

    return StreamingResponse(
        fake_stream(),
        media_type="text/event-stream"
    )
