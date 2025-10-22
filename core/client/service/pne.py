import asyncio
from typing import Union, Literal, List

from pydantic import BaseModel, Field

from common.llm.model import McpTool
from common.llm.model import PlainInputPrompt
from common.llm.openai_provider.model import OpenAIProvider, OpenAIContextManager
from common.service import CommonService
from models.request import PlanAndExecuteChattingRequest
from service.tool import ToolListService


class Step(BaseModel):
    """A class representing a single step in a multi-step plan.

    This class defines a single step or action in a larger plan, containing:
    - A detailed description explaining what this step accomplishes
    - A type of Step that describes what kind of step this step is.
    """
    desc: str = Field(..., description='Detailed description of the plan')
    type: Literal['tool_call', 'assistant'] = Field(
        default='assistant',
        description='type of Step,\nwhen calling a function is needed: tool_call\n'
                    'when assistant message is needed: assistant')


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
    
    This class is used when no further planning steps are needed
    - message: final answer for return to user, considering previous steps and answering according to user requirements
    - type: A marker indicating this object is an instance of the Response class
    """
    message: str = Field(..., description='final response message to user')
    type: Literal['response'] = Field(default="response",
                                      description="A marker indicating this object is an instance of the Response class")


class Action(BaseModel):
    """A class representing the action response in a plan-and-execute workflow.

    The response field can contain either:
    1. A Plan object: When a structured plan with multiple steps is needed to complete the task
    2. A Response object: When no more planning is required, and a final answer can be returned to the user

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

    async def _execute_tools(self, invoked_tools: list[McpTool]) -> None:
        """Execute invoked MCP tools in parallel and log results"""
        async with self.mcp_servers:
            await asyncio.gather(
                *[tool.call(client=self.mcp_servers) for tool in invoked_tools]
            )

        for tool in invoked_tools:
            self.logger.info(f"tool result: {tool}")

    async def complete(self) -> str:
        # 계획 수립을 위한 프롬프트 템플릿 생성
        main_context = OpenAIContextManager()
        main_context += (
            PlainInputPrompt(role='system', content=self.prompt_manager.planning_instruction_prompt),
            PlainInputPrompt(role='user', content=self.request.question)
        )
        main_context += await ToolListService().run(tags=[])
        output = await self.llm.structured_output_with_tools(main_context, structure=Action)

        past_step = []
        self.logger.info(f"execution plan")
        while output.response.type == 'plan':
            self.logger.info("-------------------step-execute------------------")
            self.logger.info("\tL current plan")
            for step in output.response.steps:
                self.logger.info(f"\t\tL step: {step}")

            step: Step = output.response.steps[0]
            self.logger.info(f"\tL current step: {step}")
            org_plan = output.response.steps

            if step.type == 'assistant':
                self.logger.info(f"\tL assistant step: {step.desc}")
                sub_context = OpenAIContextManager()
                plan_execute_prompt = self.prompt_manager.plan_execute_prompt.format(
                    input=self.request.question,
                    plan=org_plan, past_step='\n'.join([str(s) for s in past_step])
                )
                sub_context += [
                    PlainInputPrompt(role='system', content=plan_execute_prompt),
                    PlainInputPrompt(role='user', content=step.desc)
                ]
                output = await self.llm.structured_output(main_context, structure=Response)
                past_step.append(
                    (step.desc, output.message)
                )

            elif step.type == 'tool_call':
                main_context += self.llm.invoke_tools(main_context)
                invoked_tools = main_context.get_invoked_tools()
                if invoked_tools:
                    self.logger.info("\t\tL invoke tool")
                    await self._execute_tools(invoked_tools)
                self.logger.info(f"\tL tool call: {step.desc}")

            else:
                raise Exception(f"unknown step type: {step.type}")

            replanning_prompt = self.prompt_manager.replanning_prompt.format(
                input=self.request.question,
                plan=org_plan, past_step='\n'.join([str(s) for s in past_step])
            )
            main_context += [PlainInputPrompt(role='system', content=replanning_prompt)]
            self.logger.info(f"current prompt")
            self.logger.info(main_context)
            output = await self.llm.structured_output_with_tools(main_context, structure=Action)

        print(output.response.message)
        return output.response.message
