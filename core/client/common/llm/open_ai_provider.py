import os

from openai import OpenAI
from openai.types.responses import ResponseFunctionToolCall, ResponseOutputMessage
from openai.types.responses.function_tool_param import FunctionToolParam

from common.functional.singleton import Singleton
from common.llm.model import AvailableTool, McpTool, OutputMessage


class OpenAIProvider(metaclass=Singleton):
    def __init__(self, api_key: str = None):
        if api_key is None:
            api_key = os.environ.get('OPENAI_API_KEY')
        self.openai = OpenAI(api_key=api_key)

    @staticmethod
    def _parsing_tool_schema(tool: AvailableTool) -> FunctionToolParam:
        """
        parameter schema example:
            FunctionToolParam(
                type='function',
                name="name_of_function",
                description="description of function",
                parameters={
                    "type": "object",
                    "properties": {
                        "paramA": {
                            "type": "string",
                            "description": "parameter A",
                        }
                    },
                    "required": ["paramA"],
                    "additionalProperties": False,
                },
                strict=True
            )
        """
        schema = tool.input_schema
        properties = {"type": "object", "additionalProperties": False, 'properties': {}}
        for key in schema['properties'].keys():
            _type = schema['properties'][key].get('type')
            if _type is None:
                any_of = [input_type['type'] for input_type in schema['properties'][key].get('anyOf')]
                _type = ','.join(any_of)
            properties['properties'].update({
                key: {
                    'type': _type, 'description': schema['properties'][key].get('description', '')
                }
            })
        properties['required'] = schema.get('required')

        return FunctionToolParam(
            type='function',
            name=tool.name,
            description=tool.description,
            parameters=properties,
            strict=True
        )

    def invoke_tools(self, input_list: list[dict], available_tools: list[AvailableTool]) -> tuple[list[dict], OutputMessage, list[McpTool]]:
        """
        Invoke tools using LLM function calling.

        Returns:
            tuple containing:
                - Updated conversation history
                - Output message from LLM
                - List of invoked tools
        """
        conversation_history = input_list.copy()
        tool_schemas = [self._parsing_tool_schema(t) for t in available_tools]

        response = self.openai.responses.create(
            model='gpt-5-mini',
            tools=tool_schemas,
            input=conversation_history,
        )

        conversation_history += response.output

        invoked_tools = []
        output_message = OutputMessage()
        for output in response.output:
            if isinstance(output, ResponseFunctionToolCall):
                invoked_tools.append(McpTool.from_openai(output))
            if isinstance(output, ResponseOutputMessage):
                output_message = OutputMessage.from_openai(output)

        return conversation_history, output_message, invoked_tools

    def chat(self, input_list: list[dict], mcp_tools: list[McpTool]) -> tuple[list[dict], OutputMessage]:
        """
        Generate chat response with tool results.

        Returns:
            tuple containing:
                - Updated conversation history
                - Output message from LLM
        """
        conversation_history = input_list.copy()

        for tool in mcp_tools:
            if tool.output:
                conversation_history.append({
                    "type": "function_call_output",
                    "call_id": tool.call_id,
                    "output": tool.function_result,
                })

        response = self.openai.responses.create(
            model="gpt-5-mini",
            input=conversation_history,
        )

        for output in response.output:
            if isinstance(output, ResponseOutputMessage):
                return conversation_history, OutputMessage.from_openai(output)

        return conversation_history, OutputMessage(text="null")

    def chat_stream(self):
        ...
