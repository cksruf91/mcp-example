from fastmcp.tools import Tool
from pydantic import BaseModel, Field


class ToolListResponse(BaseModel):
    tools: list[Tool] = Field(default_factory=list, description="Tool list")


class ChatResponse(BaseModel):
    chat_id: int = Field(..., description="Chat ID")
    message: str = Field(..., description="Message")
