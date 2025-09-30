from pydantic import BaseModel, Field


class ChattingRequest(BaseModel):
    text: str = Field(default="tell me the name and address for userID M33")
