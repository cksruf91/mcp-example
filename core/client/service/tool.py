from fastmcp.tools import Tool

from common.service import ServiceClient
from models.response import ToolListResponse


class ToolListService(ServiceClient):

    def __init__(self):
        super().__init__()

    async def run(self) -> ToolListResponse:
        tool_list = ToolListResponse()
        async with self.mcp_servers:
            result: list[Tool] = await self.mcp_servers.list_tools()
            for r in result:
                tool_list.tools.append(r)
        return tool_list
