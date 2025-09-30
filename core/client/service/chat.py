import asyncio

from mcp.types import Tool

from common.llm.open_ai_provider import OpenAIProvider
from common.service import ServiceClient
from models.request import ChattingRequest
from models.response import ChatResponse


class ChatService(ServiceClient):

    def __init__(self, request: ChattingRequest):
        super().__init__()
        self.llm = OpenAIProvider()
        self.request = request
        self.logger.info(f"Initializing Service, Request: {request}")

    async def get_available_tools(self, tags: list[str]) -> list[Tool]:
        async with self.mcp_servers:
            # print(tool.meta)  # {'author': 'anonymous', '_fastmcp': {'tags': ['alpha']}}
            available_tools: list[Tool] = await self.mcp_servers.list_tools()  # TODO filtering tool
        return available_tools

    async def run(self) -> ChatResponse:

        input_list = [
            {'role': 'system', 'content': self.prompt_manager.system_prompt},
            {'role': 'user', 'content': self.request.text},
        ]
        available_tools = await self.get_available_tools(tags=[])
        output_message, invoked_tools = self.llm.invoke_tools(input_list, available_tools=available_tools)
        if not invoked_tools:
            return ChatResponse(
                chat_id=self.request.roomId,
                message=output_message.text
            )

        async with self.mcp_servers:
            await asyncio.gather(
                *[tool.call(client=self.mcp_servers) for tool in invoked_tools]
            )

        for tool in invoked_tools:
            self.logger.info(f"tool result: {tool}")

        output = self.llm.chat(input_list, mcp_tools=invoked_tools)
        return ChatResponse(chat_id=self.request.roomId, message=output.text)
