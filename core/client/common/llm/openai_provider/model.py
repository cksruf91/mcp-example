import asyncio
import os
from typing import Optional, AsyncIterable, TypeVar

from langchain_openai import ChatOpenAI
from openai import OpenAI
from openai.types.responses import (ResponseOutputMessage, ResponseOutputItem)

from common.functional.singleton import Singleton
from common.llm.openai_provider.message import OpenAIContextManager
from common.utils import get_logger

StructureT = TypeVar('StructureT')


class OpenAIProvider(metaclass=Singleton):
    def __init__(self, api_key: str = None):
        if api_key is None:
            api_key = os.environ.get('OPENAI_API_KEY')
        self.openai = OpenAI(api_key=api_key)
        self.model = "gpt-4.1-mini"
        self.logger = get_logger()

    def get_langchain_object(self, **kwargs) -> ChatOpenAI:
        """ Creates and returns an instance of ChatOpenAI configured with the specified model. """
        return ChatOpenAI(model=self.model, **kwargs)

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
            model=self.model,
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
            model=self.model,
            instructions=conversation.instruction,
            input=conversation.to_list(),
            stream=False,
        )
        self.logger.info("--------------chat_complete---------------")
        for output in response.output:
            self.logger.info(output)
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
            model=self.model,
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

    async def structured_output(self, conversation: OpenAIContextManager, structure: StructureT) -> StructureT:
        """
        Generate a structured response parsed into the provided schema.

        This calls the OpenAI Responses.parse API to coerce the model output into
        the shape of the given structure (text_format), such as a Pydantic model
        or a typed dictionary.

        Args:
            conversation: OpenAIContextManager containing conversation history and
                instructions used to guide the model.
            structure: StructureT schema/type used to parse the model output
                (e.g., a Pydantic BaseModel or a TypedDict-like structure).

        Returns:
            StructureT: Parsed structured object produced by the model.
        """
        self.logger.info("call structured_output")
        response = self.openai.responses.parse(
            model=self.model,
            instructions=conversation.instruction,
            input=conversation.to_list(),
            text_format=structure,
        )
        return response.output_parsed

    async def structured_output_with_tools(self, conversation: OpenAIContextManager,
                                           structure: StructureT) -> StructureT:
        """
        Generate a structured response (with tool results) parsed into the provided schema.

        Use this when the conversation may include prior tool invocations/results
        and you want the final model response parsed into the specified structure.
        This also utilizes the OpenAI Responses.parse API, ensuring the output
        conforms to the given schema.

        Args:
            conversation: OpenAIContextManager containing conversation history,
                tool results, and instructions.
            structure: StructureT schema/type used to parse the model output
                (e.g., a Pydantic BaseModel or a TypedDict-like structure).

        Returns:
            StructureT: Parsed structured object produced by the model.
        """
        self.logger.info("call structured_output_with_tools")
        response = self.openai.responses.parse(
            model=self.model,
            instructions=conversation.instruction,
            tools=conversation.get_available_tools(),
            input=conversation.to_list(),
            text_format=structure,
        )
        return response.output_parsed
