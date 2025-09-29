import json
from typing import Any

from fastmcp.client.client import CallToolResult
from fastmcp import Client
from openai.types.responses import ResponseFunctionToolCall, ResponseOutputMessage
from pydantic import BaseModel, Field


class McpTool(BaseModel):
    call_id: str = Field(...)
    function_name: str = Field(...)
    function_param: dict[str, Any] = Field(...)
    output: Any = None

    async def call(self, client: Client):
        output: CallToolResult = await client.call_tool(self.function_name, self.function_param)
        self.output = json.dumps(output.data)

    @classmethod
    def from_openai(cls, invoked_tool: ResponseFunctionToolCall) -> "McpTool":
        return cls(
            call_id=invoked_tool.call_id,
            function_name=invoked_tool.name,
            function_param=json.loads(invoked_tool.arguments),
        )


class OutputMessage(BaseModel):
    text: str = Field(default=None)

    @classmethod
    def from_openai(cls, message: ResponseOutputMessage) -> "OutputMessage":
        return cls(text=message.content[0].text)
