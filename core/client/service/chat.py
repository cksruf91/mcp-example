import asyncio
from typing import AsyncIterable

from common.llm.model import McpTool, PlainInputPrompt
from common.llm.openai_provider.message import OpenAIContextManager
from common.llm.openai_provider.model import OpenAIProvider
from common.service import CommonService
from models.request import ChattingRequest
from service.tool import ToolListService


class ChatService(CommonService):

    def __init__(self, request: ChattingRequest):
        super().__init__(room_id=request.roomId)
        self.llm = OpenAIProvider()
        self.request = request
        self.logger.info(f"Initializing Service, Request: {request}")

    def _initialize_conversation(self) -> list[PlainInputPrompt]:
        """Initialize conversation history with system prompt and user message"""
        return [
            PlainInputPrompt(role='system', content=self.prompt_manager.system_prompt),
            PlainInputPrompt(role='user', content=self.request.text)
        ]

    async def _execute_tools(self, invoked_tools: list[McpTool]) -> None:
        """Execute invoked MCP tools in parallel and log results"""
        async with self.mcp_servers:
            await asyncio.gather(
                *[tool.call(client=self.mcp_servers) for tool in invoked_tools]
            )

        for tool in invoked_tools:
            self.logger.info(f"tool result: {tool}")

    async def _process_request(self) -> OpenAIContextManager:
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
        context = OpenAIContextManager()
        context += self._initialize_conversation()
        context += await ToolListService().run(tags=[])
        context += self.llm.invoke_tools(context)
        return context

    async def complete(self) -> str:
        context = await self._process_request()
        invoked_tools = context.get_invoked_tools()
        if not invoked_tools:
            self.logger.info(context)
            last_assistant_message = context.get_last_assistant_message()
            return last_assistant_message.content

        await self._execute_tools(invoked_tools)
        self.logger.info(context)
        output = self.llm.chat_complete(context)
        return output.content[0].text

    async def stream(self) -> AsyncIterable[str]:
        context = await self._process_request()
        invoked_tools = context.get_invoked_tools()
        if not invoked_tools:
            self.logger.info(context)
            last_assistant_message = context.get_last_assistant_message()
            yield last_assistant_message.content
            return

        await self._execute_tools(invoked_tools)
        self.logger.info(context)
        self.logger.info("start generating message")
        async for event in self.llm.chat_stream(context):
            yield event
        self.logger.info("EOF")
        return
