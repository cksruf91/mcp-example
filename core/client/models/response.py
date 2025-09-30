from mcp.types import Tool
from pydantic import BaseModel, Field


class ToolListResponse(BaseModel):
    tools: list[Tool] = Field(default_factory=list, description="Tool list")


class ChatResponse(BaseModel):
    chat_id: str = Field(..., description="Room ID")
    message: str = Field(..., description="Message")
