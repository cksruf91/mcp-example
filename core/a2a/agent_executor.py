from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import Message as A2aMessage
from a2a.utils import new_agent_text_message
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.models.openai import OpenAIModel
from strands.tools.executors import ConcurrentToolExecutor
from strands.tools.mcp.mcp_client import MCPClient, MCPAgentTool
from strands.types.content import Message, ContentBlock


class ToolService:
    def __init__(self):
        self.alpha = MCPClient(lambda: streamablehttp_client("http://localhost:9011/mcp"))
        self.beta = MCPClient(lambda: streamablehttp_client("http://localhost:9012/mcp"))

    def list_tools(self) -> list[MCPAgentTool]:
        tools: list[MCPAgentTool] = []
        with self.alpha, self.beta:
            tools += self.alpha.list_tools_sync()
            tools += self.beta.list_tools_sync()
        return tools


class HelloWorldAgent:
    """Hello World Agent."""

    def __init__(self):
        self.tool_service = ToolService()

        model = OpenAIModel(
            model_id="gpt-4o-mini",
            params={
                "temperature": 0.1,
            }
        )
        self.llm = Agent(
            model=model,
            tools=self.tool_service.list_tools(),
            tool_executor=ConcurrentToolExecutor(),
            system_prompt="You are a helpful assistant."
        )

    async def invoke(self, a2a_message: A2aMessage) -> str:

        message = Message(role='user', content=[])
        for part in a2a_message.parts:
            if part.root.kind == "text":
                message['content'].append(
                    ContentBlock(text=part.root.text)
                )

        with self.tool_service.alpha, self.tool_service.beta:
            result = self.llm([message])

        # Access metrics through the AgentResult
        print(f"Total tokens: {result.metrics.accumulated_usage['totalTokens']}")
        print(f"Execution time: {sum(result.metrics.cycle_durations):.2f} seconds")
        print(f"Tools used: {list(result.metrics.tool_metrics.keys())}")
        return result.message['content'][0]['text']


class HelloWorldAgentExecutor(AgentExecutor):
    """Test AgentProxy Implementation."""

    def __init__(self):
        self.agent = HelloWorldAgent()

    async def execute(
            self,
            context: RequestContext,
            event_queue: EventQueue,
    ) -> None:
        result = await self.agent.invoke(context.message)
        await event_queue.enqueue_event(new_agent_text_message(result))

    async def cancel(
            self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise Exception('cancel not supported')
