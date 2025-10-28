import asyncio
import operator
from typing import Annotated, List, Tuple

from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import END
from langgraph.graph import StateGraph, START
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from common.llm.model import McpTool
from common.llm.openai_provider.model import OpenAIProvider
from common.prompt import PromptManager
from common.service import CommonService
from models.request import PlanAndExecuteChattingRequest


class PlanExecute(TypedDict):
    input: str
    plan: List[str]
    past_steps: Annotated[List[Tuple], operator.add]
    response: str


class Plan(BaseModel):
    """Plan to follow in future"""

    steps: List[str] = Field(
        description="different steps to follow, should be in sorted order"
    )


class Response(BaseModel):
    """Response to user."""

    response: str


class Act(BaseModel):
    """Action to perform."""

    action: Response | Plan = Field(
        description="Action to perform. If you want to respond to user, use Response. "
                    "If you need to further use tools to get the answer, use Plan."
    )


class AgentBuilder:

    def __init__(self, prompt_manager: PromptManager):
        self.prompt_manager = prompt_manager
        self.client = MultiServerMCPClient(
            {
                "alpha": {
                    "url": "http://localhost:9011/mcp",
                    "transport": "streamable_http",
                },
                "beta": {
                    "url": "http://localhost:9012/mcp",
                    "transport": "streamable_http",
                },
                "resource": {
                    "url": "http://localhost:9013/mcp",
                    "transport": "streamable_http",
                }
            }
        )

    async def build_task_execute_agent(self) -> CompiledStateGraph:
        llm = OpenAIProvider().get_langchain_object(temperature=0)
        tools = await self.client.get_tools()
        return create_agent(llm, tools=tools, system_prompt=self.prompt_manager.langchain_task_executor)

    async def build_planning_agent(self):
        llm = OpenAIProvider().get_langchain_object(temperature=0)
        planner_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system", self.prompt_manager.langchain_planner,
                ),
                ("placeholder", "{messages}"),
            ]
        )
        return planner_prompt | llm.with_structured_output(Plan)

    async def build_re_planning_agent(self):
        llm = OpenAIProvider().get_langchain_object(temperature=0)
        re_planner_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system", self.prompt_manager.langchain_replanner,
                ),
                ("placeholder", "{messages}"),
            ]
        )
        return re_planner_prompt | llm.with_structured_output(Act)


class PlanAndExecuteChatService(CommonService):

    def __init__(self, request: PlanAndExecuteChattingRequest):
        super().__init__(room_id=request.roomId)
        self.request = request
        self.builder = AgentBuilder(self.prompt_manager)
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
        executor = await self.builder.build_task_execute_agent()
        planner = await self.builder.build_planning_agent()
        re_planner = await self.builder.build_re_planning_agent()

        async def execute_step(state: PlanExecute):
            plan = state["plan"]
            plan_str = "\n".join(f"{i + 1}. {step}" for i, step in enumerate(plan))
            task = plan[0]
            task_formatted = f"""For the following plan:
        {plan_str}\n\nYou are tasked with executing step {1}, {task}."""
            agent_response = await executor.ainvoke(
                {"messages": [("user", task_formatted)]}
            )
            print("\t" + repr(agent_response))
            return {
                "past_steps": [(task, agent_response["messages"][-1].content)],
            }

        async def plan_step(state: PlanExecute):
            plan = await planner.ainvoke({"messages": [("user", state["input"])]})
            return {"plan": plan.steps}

        async def replan_step(state: PlanExecute):
            output = await re_planner.ainvoke(state)
            if isinstance(output.action, Response):
                return {"response": output.action.response}
            else:
                return {"plan": output.action.steps}

        def should_end(state: PlanExecute):
            if "response" in state and state["response"]:
                return END
            else:
                return "agent"

        workflow = StateGraph(PlanExecute)

        # Add the plan node
        workflow.add_node("planner", plan_step)

        # Add the execution step
        workflow.add_node("agent", execute_step)

        # Add a replan node
        workflow.add_node("replan", replan_step)

        workflow.add_edge(START, "planner")

        # From plan we go to agent
        workflow.add_edge("planner", "agent")

        # From agent, we replan
        workflow.add_edge("agent", "replan")

        workflow.add_conditional_edges(
            "replan",
            # Next, we pass in the function that will determine which node is called next.
            should_end,
            ["agent", END],
        )

        # Finally, we compile it!
        # This compiles it into a LangChain Runnable,
        # meaning you can use it as you would any other runnable
        app = workflow.compile()
        config = {"recursion_limit": 50}
        inputs = {"input": self.request.question}
        async for event in app.astream(inputs, config=config):
            for k, v in event.items():
                print("================================================")
                print(k, v)
                # if k != "__end__":
                #     print(v)
        return v['response']
