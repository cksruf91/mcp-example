import json
from typing import Any

from fastmcp.client.client import CallToolResult
from openai.types.responses import ResponseFunctionToolCall, ResponseOutputMessage
from pydantic import BaseModel, Field


class Tool(BaseModel):
    call_id: str = Field(...)
    function_name: str = Field(...)
    function_param: dict[str, Any] = Field(...)


class InvokedTools(BaseModel):
    tools: list[Tool] = Field(default_factory=list)

    def __len__(self) -> int:
        return len(self.tools)

    @classmethod
    def init_from_openai(cls, invoke_from_openai: list[ResponseFunctionToolCall]) -> "InvokedTools":
        tools = []
        for invoked in invoke_from_openai:
            print(invoked)
            tools.append(
                Tool(
                    call_id=invoked.call_id,
                    function_name=invoked.name,
                    function_param=json.loads(invoked.arguments)
                )
            )
        return cls(tools=tools)


class TextMessage(BaseModel):
    text: str = Field(default=None)

    @classmethod
    def init_from_openai(cls, message: ResponseOutputMessage) -> "TextMessage":
        return cls(text=message.content[0].text)


class ToolOutput(BaseModel):
    call_id: str = Field(...)
    tool_output: CallToolResult = Field(...)

    def get_input_message(self):
        return {
            "type": "function_call_output",
            "call_id": self.call_id,
            "output": json.dumps(self.tool_output.data)
        }
