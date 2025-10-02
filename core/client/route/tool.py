from fastapi import APIRouter, Query

from models.response import ToolListResponse
from service.tool import ToolListService

tool_router = APIRouter(prefix='/tool', tags=['tool'])


@tool_router.get('/list')
async def get_tool_list(tags: list[str] = Query(default=[])):
    tool_list = await ToolListService().run(tags=tags)
    return ToolListResponse(tools=tool_list)
