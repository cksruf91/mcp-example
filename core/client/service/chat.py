import asyncio
from typing import AsyncIterable

from common.llm.model import AvailableTool
from common.llm.open_ai_provider import OpenAIProvider
from common.service import CommonService
from models.request import ChattingRequest


class ChatService(CommonService):

    def __init__(self, request: ChattingRequest):
        super().__init__(room_id=request.roomId)
        self.llm = OpenAIProvider()
        self.request = request
        self.logger.info(f"Initializing Service, Request: {request}")

    async def get_available_tools(self, tags: list[str]) -> list[AvailableTool]:
        """Get available tools from MCP servers, optionally filtered by tags"""
        async with self.mcp_servers:
            available_tools = [AvailableTool(tool) for tool in await self.mcp_servers.list_tools()]
            if tags:
                available_tools = [tool for tool in available_tools if tool.has_any_tags(tags)]

        return available_tools

    async def run(self) -> str:

        conversation_history = [
            {'role': 'system', 'content': self.prompt_manager.system_prompt},
            {'role': 'user', 'content': self.request.text},
        ]

        available_tools = await self.get_available_tools(tags=[])
        conversation_history, output_message, invoked_tools = self.llm.invoke_tools(
            conversation_history,
            available_tools=available_tools
        )

        if not invoked_tools:
            return output_message.text

        async with self.mcp_servers:
            await asyncio.gather(
                *[tool.call(client=self.mcp_servers) for tool in invoked_tools]
            )

        for tool in invoked_tools:
            self.logger.info(f"tool result: {tool}")

        _, output = self.llm.chat(conversation_history, mcp_tools=invoked_tools)
        return output.text

    async def stream(self) -> AsyncIterable[str]:
        conversation_history = [
            {'role': 'system', 'content': self.prompt_manager.system_prompt},
            {'role': 'user', 'content': self.request.text},
        ]

        available_tools = await self.get_available_tools(tags=[])
        conversation_history, output_message, invoked_tools = self.llm.invoke_tools(
            conversation_history,
            available_tools=available_tools
        )

        if not invoked_tools:
            yield output_message.text
            return

        async with self.mcp_servers:
            await asyncio.gather(
                *[tool.call(client=self.mcp_servers) for tool in invoked_tools]
            )

        for tool in invoked_tools:
            self.logger.info(f"tool result: {tool}")

        self.logger.info("start generating message")
        async for event in self.llm.chat_stream(conversation_history, mcp_tools=invoked_tools):
            yield event
        self.logger.info("EOF")
        return
