from fastmcp.tools import Tool

from common.llm.open_ai_provider import OpenAIProvider
from common.llm.provider import ToolOutput
from common.service import ServiceClient
from models.request import ChattingRequest
from models.response import ChatResponse


class ChatService(ServiceClient):
    openai = OpenAIProvider()

    def __init__(self, request: ChattingRequest):
        super().__init__()
        self.request = request

    async def run(self) -> ChatResponse:

        input_list = [
            {'role': 'system', 'content': self.prompt_manager.system_prompt},
            {'role': 'user', 'content': self.request.text},
        ]

        async with self.mcp_servers:
            result: list[Tool] = await self.mcp_servers.list_tools()
        output_message, invoked_tools = self.openai.invoke_tools(input_list, available_tools=result)
        if not invoked_tools:
            return ChatResponse(
                chat_id=1,
                message=output_message.text
            )

        async with self.mcp_servers:
            for tool in invoked_tools.tools:
                tool_result = await self.mcp_servers.call_tool(tool.function_name, tool.function_param)
                input_list.append(
                    ToolOutput(
                        call_id=tool.call_id,
                        tool_output=tool_result,
                    ).get_input_message()
                )

        output = self.openai.chat(input_list)
        return ChatResponse(chat_id=1, message=output)
