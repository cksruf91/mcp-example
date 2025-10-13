import asyncio
import os
from typing import Optional, AsyncIterable

from openai import OpenAI
from openai.types.responses import (ResponseOutputMessage, ResponseOutputItem)

from common.functional.singleton import Singleton
from common.llm.openai_provider.message import OpenAIContextManager


class OpenAIProvider(metaclass=Singleton):
    def __init__(self, api_key: str = None):
        if api_key is None:
            api_key = os.environ.get('OPENAI_API_KEY')
        self.openai = OpenAI(api_key=api_key)

    def invoke_tools(self, conversation: OpenAIContextManager) -> list[ResponseOutputItem]:
        """
        Invoke tools using LLM function calling.

        Args:
            conversation: OpenAIContextManager containing conversation history and available tools

        Returns:
            list[ResponseOutputItem]: List of output items from LLM response, including
                messages and function tool calls
        """

        response = self.openai.responses.create(
            model='gpt-5-mini',
            instructions=conversation.instruction,
            tools=conversation.get_available_tools(),
            input=conversation.to_list(),
            stream=False,
        )
        return response.output

    def chat_complete(self, conversation: OpenAIContextManager) -> Optional[ResponseOutputMessage]:
        """
        Generate chat response with tool results.

        Args:
            conversation: OpenAIContextManager containing conversation history with tool results

        Returns:
            Optional[ResponseOutputMessage]: Message output from LLM, or None if no message
                output is found in the response
        """
        response = self.openai.responses.create(
            model="gpt-5-mini",
            instructions=conversation.instruction,
            input=conversation.to_list(),
            stream=False,
        )
        print("--------------chat_complete---------------")
        for output in response.output:
            print(output)
            if output.type == 'message':
                return output
        return None

    async def chat_stream(self, conversation: OpenAIContextManager) -> AsyncIterable[str]:
        """
        Generate streaming chat response with tool results.

        Yields:
            str: Text chunks from the streaming response
        """
        stream = self.openai.responses.create(
            model="gpt-5-mini",
            instructions=conversation.instruction,
            input=conversation.to_list(),
            stream=True,
        )

        for event in stream:
            await asyncio.sleep(0.01)
            if event.type == 'response.created':
                yield ""
            elif hasattr(event, 'delta'):
                yield event.delta
            elif event.type == 'response.completed':
                return
        return
