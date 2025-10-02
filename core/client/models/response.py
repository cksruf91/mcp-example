from pydantic import BaseModel, Field

from common.llm.model import AvailableTool


class ToolListResponse(BaseModel):
    tools: list[AvailableTool] = Field(default_factory=list, description="Tool list")


class ChatResponse(BaseModel):
    roomId: str = Field(..., description="Room ID")
    message: str = Field(..., description="Message")
