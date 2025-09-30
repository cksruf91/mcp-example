import uuid

from pydantic import BaseModel, Field


class ChattingRequest(BaseModel):
    text: str = Field(default="tell me the name and address for userID M4386")
    roomId: str = Field(default_factory=lambda: str(uuid.uuid4()))
