from fastmcp.tools import Tool

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

    async def run(self) -> ChatResponse:

        input_list = [
            {'role': 'system', 'content': self.prompt_manager.system_prompt},
            {'role': 'user', 'content': self.request.text},
        ]
        async with self.mcp_servers:
            available_tools: list[Tool] = await self.mcp_servers.list_tools()
        output_message, invoked_tools = self.llm.invoke_tools(input_list, available_tools=available_tools)
        if not invoked_tools:
            return ChatResponse(
                chat_id=1,
                message=output_message.text
            )

        async with self.mcp_servers:
            for tool in invoked_tools:  # TODO: get tool result asynchronously
                await tool.call(client=self.mcp_servers)

        output = self.llm.chat(input_list, tools=invoked_tools)
        return ChatResponse(chat_id=1, message=output.text)
