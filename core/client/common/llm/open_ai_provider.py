import os

from fastmcp.tools import Tool
from openai import OpenAI
from openai.types.responses import ResponseFunctionToolCall, ResponseOutputMessage
from openai.types.responses.function_tool_param import FunctionToolParam

from common.llm.provider import InvokedTools, TextMessage


class OpenAIProvider:
    def __init__(self):
        self.openai = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

    @staticmethod
    def _parsing_tool_schema(tool: Tool) -> FunctionToolParam:
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
        schema = tool.inputSchema
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

    def invoke_tools(self, input_list: list[dict], available_tools: list[Tool]) -> tuple[TextMessage, InvokedTools]:
        available_tools = [self._parsing_tool_schema(t) for t in available_tools]
        response = self.openai.responses.create(
            model='gpt-5-mini',
            tools=available_tools,
            input=input_list,
        )

        input_list += response.output

        invoked_tools = []
        output_message = TextMessage()
        for output in response.output:
            if isinstance(output, ResponseFunctionToolCall):
                invoked_tools.append(output)
            if isinstance(output, ResponseOutputMessage):
                output_message = TextMessage.init_from_openai(output)

        return output_message, InvokedTools.init_from_openai(invoked_tools)

    def chat(self, input_list: list[dict]) -> str:
        response = self.openai.responses.create(
            model="gpt-5-mini",
            instructions="Respond to user base on function call result",
            input=input_list,
        )
        for output in response.output:
            if isinstance(output, ResponseOutputMessage):
                return output.content[0].text
        return "null"

    def chat_stream(self):
        ...
