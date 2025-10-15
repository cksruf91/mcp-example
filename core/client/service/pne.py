from typing import Union, Literal, List

from pydantic import BaseModel, Field

from common.llm.model import PlainInputPrompt
from common.llm.openai_provider.model import OpenAIProvider, OpenAIContextManager
from common.service import CommonService
from models.request import PlanAndExecuteChattingRequest


class Step(BaseModel):
    """A class representing a single step in a multi-step plan.

    This class defines a single step or action in a larger plan, containing:
    - A detailed description explaining what this step accomplishes
    - A command prompt that will be executed to carry out this step
    """
    desc: str = Field(..., description='Detailed description of the plan')
    prompt: str = Field(..., description='Command prompt for executing the plan')


class Plan(BaseModel):
    """
    Represents a structured plan consisting of multiple steps.
    The steps must be executed in sequential order, with each step building upon the completion of the previous step.
    """
    steps: List[Step] = Field(..., description='List of steps to execute')
    type: Literal['plan'] = Field(default="plan",
                                  description="A marker indicating this object is an instance of the Plan class")


class Response(BaseModel):
    """
    A class representing a final response in the plan-and-execute workflow.
    
    This class is used when no further planning steps are needed and a final answer
    can be returned to the user. It extends BaseModel to provide validation and
    serialization capabilities.
    """
    message: str = Field(..., description='The response message')
    type: Literal['response'] = Field(default="response",
                                      description="A marker indicating this object is an instance of the Response class")


class Action(BaseModel):
    """A class representing the action response in a plan-and-execute workflow.

    The response field can contain either:
    1. A Plan object: When a structured plan with multiple steps is needed to complete the task
    2. A Response object: When no more planning is required and a final answer can be returned to the user

    Each Plan object contains sequential steps that need to be executed in order,
    while a Response object contains the final answer to be returned to the user.
    """
    response: Union[Plan, Response] = Field(..., description="Plan or Response to this action")


class PlanAndExecuteChatService(CommonService):

    def __init__(self, request: PlanAndExecuteChattingRequest):
        super().__init__(room_id=request.roomId)
        self.llm = OpenAIProvider()
        self.request = request
        self.logger.info(f"Initializing Service, Request: {request}")

    async def complete(self) -> str:
        # 계획 수립을 위한 프롬프트 템플릿 생성
        main_context = OpenAIContextManager()
        main_context += (
            PlainInputPrompt(role='system', content=self.prompt_manager.planning_instruction_prompt),
            PlainInputPrompt(role='user', content=self.request.question)
        )
        self.logger.info("planner prompt set")
        output = await self.llm.structured_output(main_context, structure=Action)
        if output.response.type == 'plan':
            print('-------- first plan ---------')
            for step in output.response.steps:
                print(step)
        self.logger.info("planner created")

        while output.response.type == 'plan':
            step = output.response.steps.pop(0)
            org_plan = output.response.steps
            context = OpenAIContextManager()
            context.append(PlainInputPrompt(role='user', content=step.prompt))
            output = await self.llm.structured_output(context, structure=Response)
            print('-------- execute plan result ---------')
            print(output.message)

            replanning_prompt = self.prompt_manager.replanning_prompt.format(
                input=self.request.question,
                plan=org_plan,
                past_steps=(step.prompt, output.message)
            )
            print('-------- replanning prompt ---------')
            context = OpenAIContextManager()
            context.append(PlainInputPrompt(role='user', content=replanning_prompt))
            print(context)
            output = await self.llm.structured_output(context, structure=Action)
            print(output)

        print('-------- final answer ---------')
        print(output.response.message)
        return output.response.message
