from pydantic import BaseModel, Field


class ChattingRequest(BaseModel):
    text: str = Field(default="plz add these two number 3.24, 44.23")
