import uuid

from pydantic import BaseModel, Field


class ChattingRequest(BaseModel):
    question: str = Field(default="tell me the name and address for userID M4386")
    roomId: str = Field(default_factory=lambda: str(uuid.uuid4()))


class PlanAndExecuteChattingRequest(BaseModel):
    question: str = Field(
        default="Tell me the name of user 'M4386', "
                "their reserved product list, the detailed information of the reserved products, "
                "and the total sum of the prices"
    )
    roomId: str = Field(default_factory=lambda: str(uuid.uuid4()))
