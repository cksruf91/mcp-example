import json
from typing import Any

from fastmcp import Client
from mcp.types import CallToolResult, TextContent
from openai.types.responses import ResponseFunctionToolCall, ResponseOutputMessage
from pydantic import BaseModel, Field


class McpTool(BaseModel):
    call_id: str = Field(...)
    function_name: str = Field(...)
    function_param: dict[str, Any] = Field(...)
    output: list[Any] = Field(default_factory=list)

    async def call(self, client: Client):
        output: CallToolResult = await client.call_tool_mcp(self.function_name, self.function_param)
        for content in output.content:
            if isinstance(content, TextContent):
                self.output.append(content.text)

    @classmethod
    def from_openai(cls, invoked_tool: ResponseFunctionToolCall) -> "McpTool":
        return cls(
            call_id=invoked_tool.call_id,
            function_name=invoked_tool.name,
            function_param=json.loads(invoked_tool.arguments),
        )

    @property
    def function_result(self) -> str:
        return json.dumps(self.output)


class OutputMessage(BaseModel):
    text: str = Field(default=None)

    @classmethod
    def from_openai(cls, message: ResponseOutputMessage) -> "OutputMessage":
        return cls(text=message.content[0].text)
