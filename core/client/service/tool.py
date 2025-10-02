from common.llm.model import AvailableTool
from common.service import CommonService


class ToolListService(CommonService):

    def __init__(self):
        super().__init__()

    async def run(self, tags: list[str] = None) -> list[AvailableTool]:
        tool_list = []
        async with self.mcp_servers:
            available_tools = [AvailableTool(tool) for tool in await self.mcp_servers.list_tools()]

            if tags:
                available_tools = [tool for tool in available_tools if tool.has_any_tags(tags)]

            for tool in available_tools:
                tool_list.append(tool)

        return tool_list
