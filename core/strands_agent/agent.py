import logging
import uuid
from typing import Literal

from mcp.client.streamable_http import streamablehttp_client
from pydantic import BaseModel, Field
from strands import Agent
from strands.models.openai import OpenAIModel
from strands.tools.executors import ConcurrentToolExecutor
from strands.tools.mcp.mcp_client import MCPClient, MCPAgentTool
from strands.types.content import Message, ContentBlock

# Configure the root strands logger
logging.getLogger("strands").setLevel(logging.DEBUG)
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)


class PlanAndExecuteChattingRequest(BaseModel):
    question: str = Field(
        default="안녕?"
    )
    roomId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    history: list[tuple[Literal['user', 'assistant'], str]] = Field(
        default_factory=lambda: [],
        description="chat history, format: [(\"user\",\"hello\"), (\"assistant\": \"hi! how are you doing?\nhow can i help you?\")]"
    )


class ChatResponse(BaseModel):
    message: str = Field()
    roomId: str = Field()


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


class PlanAndExecuteChatService:
    def __init__(self, request: PlanAndExecuteChattingRequest):
        self.request = request
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

    async def complete(self) -> str:
        with self.tool_service.alpha, self.tool_service.beta:
            mms = Message(role='user', content=[ContentBlock(text=self.request.question)])
            result = self.llm([mms])

        # Access metrics through the AgentResult
        print(f"Total tokens: {result.metrics.accumulated_usage['totalTokens']}")
        print(f"Execution time: {sum(result.metrics.cycle_durations):.2f} seconds")
        print(f"Tools used: {list(result.metrics.tool_metrics.keys())}")
        return result.message['content'][0]['text']
