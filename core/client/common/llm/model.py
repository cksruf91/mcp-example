import json
from typing import Any

from fastmcp import Client
from mcp.types import CallToolResult, TextContent, Tool
from openai.types.responses import ResponseFunctionToolCall, ResponseOutputMessage
from pydantic import BaseModel, Field


class AvailableTool(BaseModel):
    """Represents an available MCP tool that can be invoked"""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    input_schema: dict[str, Any] = Field(..., description="Tool input schema")
    tags: list[str] = Field(default_factory=list, description="Tool tags")
    meta: dict[str, Any] = Field(default_factory=dict, description="Tool metadata")

    def __init__(self, tool: Tool = None, **kwargs):
        """Initialize from MCP Tool or direct parameters"""
        if tool is not None:
            tags = tool.meta.get('_fastmcp', {}).get('tags', []) if tool.meta else []
            super().__init__(
                name=tool.name,
                description=tool.description,
                input_schema=tool.inputSchema,
                tags=tags,
                meta=tool.meta or {}
            )
        else:
            super().__init__(**kwargs)
        self._tool = tool

    def __repr__(self):
        return repr(self._tool)

    def has_tag(self, tag: str) -> bool:
        """Check if tool has specific tag"""
        return tag in self.tags

    def has_any_tags(self, tags: list[str]) -> bool:
        """Check if tool has any of the specified tags"""
        return any(self.has_tag(tag) for tag in tags)


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
