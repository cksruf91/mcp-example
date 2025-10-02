import asyncio
from typing import AsyncIterable

from common.llm.model import McpTool, OutputMessage
from common.llm.open_ai_provider import OpenAIProvider
from common.service import CommonService
from models.request import ChattingRequest
from service.tool import ToolListService


class ChatService(CommonService):

    def __init__(self, request: ChattingRequest):
        super().__init__(room_id=request.roomId)
        self.llm = OpenAIProvider()
        self.request = request
        self.logger.info(f"Initializing Service, Request: {request}")

    def _initialize_conversation(self) -> list[dict]:
        """Initialize conversation history with system prompt and user message"""
        return [
            {'role': 'system', 'content': self.prompt_manager.system_prompt},
            {'role': 'user', 'content': self.request.text},
        ]

    async def _execute_tools(self, invoked_tools: list[McpTool]) -> None:
        """Execute invoked MCP tools in parallel and log results"""
        async with self.mcp_servers:
            await asyncio.gather(
                *[tool.call(client=self.mcp_servers) for tool in invoked_tools]
            )

        for tool in invoked_tools:
            self.logger.info(f"tool result: {tool}")

    async def _process_request(self) -> tuple[list[dict], OutputMessage, list[McpTool]]:
        """
        Common workflow for processing chat request:
        1. Initialize conversation
        2. Get available tools
        3. Invoke tools via LLM

        Returns:
            tuple containing:
                - conversation history
                - output message
                - invoked tools
        """
        conversation_history = self._initialize_conversation()
        available_tools = await ToolListService().run(tags=[])
        conversation_history, output_message, invoked_tools = self.llm.invoke_tools(
            conversation_history,
            available_tools=available_tools
        )
        return conversation_history, output_message, invoked_tools

    async def complete(self) -> str:
        conversation_history, output_message, invoked_tools = await self._process_request()

        if not invoked_tools:
            return output_message.text

        await self._execute_tools(invoked_tools)

        _, output = self.llm.chat_complete(conversation_history, mcp_tools=invoked_tools)
        return output.text

    async def stream(self) -> AsyncIterable[str]:
        conversation_history, output_message, invoked_tools = await self._process_request()

        if not invoked_tools:
            yield output_message.text
            return

        await self._execute_tools(invoked_tools)

        self.logger.info("start generating message")
        async for event in self.llm.chat_stream(conversation_history, mcp_tools=invoked_tools):
            yield event
        self.logger.info("EOF")
        return
