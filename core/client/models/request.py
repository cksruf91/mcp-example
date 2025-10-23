import uuid
from typing import Literal

from pydantic import BaseModel, Field


class ChattingRequest(BaseModel):
    question: str = Field(default="tell me the name and address for userID M4386")
    roomId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    history: list[tuple[Literal['user', 'assistant'], str]] = Field(
        default_factory=lambda: [],
        description="chat history, format: [(\"user\",\"hello\"), (\"assistant\": \"hi! how are you doing?\nhow can i help you?\")]"
    )


class PlanAndExecuteChattingRequest(BaseModel):
    question: str = Field(
        default="Tell me the name of user 'M4386', "
                "their reserved product list, the detailed information of the reserved products, "
                "and the total sum of the prices"
    )
    roomId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    history: list[tuple[Literal['user', 'assistant'], str]] = Field(
        default_factory=lambda: [],
        description="chat history, format: [(\"user\",\"hello\"), (\"assistant\": \"hi! how are you doing?\nhow can i help you?\")]"
    )
