import uuid

from pydantic import BaseModel, Field


class ChattingRequest(BaseModel):
    text: str = Field(default="tell me the name and address for userID M4386")
    roomId: str = Field(default_factory=lambda: str(uuid.uuid4()))


class PlanAndExecuteChattingRequest(BaseModel):
    question: str = Field(default="LangGraph 의 핵심 장단점과 LangGraph 를 사용하는 이유는 무엇인가?")
    roomId: str = Field(default_factory=lambda: str(uuid.uuid4()))
