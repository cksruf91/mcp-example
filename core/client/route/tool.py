from fastapi import APIRouter

from service.tool import ToolListService

tool_router = APIRouter(prefix='/tool', tags=['tool'])


@tool_router.get('/list')
async def get_tool_list():
    return await ToolListService().run()
