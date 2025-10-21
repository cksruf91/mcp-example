import json
from typing import Any, TypeAlias, Union, Annotated, Optional

from openai.types.responses import ResponseFunctionToolCall, FunctionToolParam

from common.llm.model import AvailableTool, McpTool, OutputMessage, PlainInputPrompt

Prompts: TypeAlias = Annotated[
    Union[
        McpTool,
        PlainInputPrompt,
        OutputMessage,
        ResponseFunctionToolCall,
    ],
    'prompts'
]


def _to_open_ai_function_tool_param(param: AvailableTool) -> FunctionToolParam:
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
            strict=True)
    """
    schema = param.input_schema
    properties = {
        "name": param.name,
        "description": param.description,
        "type": "object",
        "additionalProperties": False,
        "properties": {}
    }
    for key in schema['properties'].keys():
        _type = schema['properties'][key].get('type')
        properties['properties'].update({
            key: {
                'type': _type,
                'description': schema['properties'][key].get('description', '')
            }
        })
        if _type == 'array':
            properties['properties'][key].update({
                'items': schema['properties'][key]['items']
            })
    properties['required'] = schema.get('required')

    return FunctionToolParam(
        type='function',
        name=param.name,
        description=param.description,
        parameters=properties,
        strict=param.strict,
    )


class OpenAIContextManager:
    def __init__(self):
        self.prompts: list[Prompts] = []
        self.available_tools: list[AvailableTool] = []
        self.instruction: Optional[str] = None

    def __add__(self, other: list) -> 'OpenAIContextManager':
        for _other in other:
            self.append(_other)
        return self

    def __repr__(self):
        _text = "[OpenAIContextManager]\n"
        _text += "\t" + f"[instruction]: {self.instruction}" + "\n"
        for prompt in self.to_list():
            _text += "\t" + repr(prompt) + '\n'
        _text += "\t" + f"[Available Tools]" + "\n"
        for tool in self.available_tools:
            _text += "\t" + repr(tool) + '\n'
        return _text

    def get_invoked_tools(self) -> list[McpTool]:
        invoked_tools = []
        for p in self.prompts:
            if isinstance(p, McpTool) and (not p.output):
                invoked_tools.append(p)
        return invoked_tools

    def get_available_tools(self) -> list[FunctionToolParam]:
        function_tool_call_params = []
        for tool in self.available_tools:
            function_tool_call_params.append(_to_open_ai_function_tool_param(tool))
        return function_tool_call_params

    def get_last_assistant_message(self) -> PlainInputPrompt:
        message = []
        for prompt in self.prompts:
            if isinstance(prompt, PlainInputPrompt) and prompt.role == 'assistant':
                message.append(prompt)
        return message[-1]

    def append(self, prompt: Any):
        prompt_type = getattr(prompt, 'type', None)
        if (prompt_type is None) or (prompt_type == 'custom_message'):
            if isinstance(prompt, AvailableTool):
                self.available_tools.append(prompt)
            elif isinstance(prompt, PlainInputPrompt) and prompt.role == 'system':
                self.instruction = prompt.content
            else:
                self.prompts.append(prompt)

        elif prompt_type == 'function_call':
            self.prompts.append(prompt)
            self.prompts.append(
                McpTool(
                    call_id=prompt.call_id,
                    function_name=prompt.name,
                    function_param=json.loads(prompt.arguments),
                )
            )
        elif prompt_type == 'message':
            self.prompts.append(
                PlainInputPrompt(
                    role=prompt.role, content=prompt.content[0].text
                )
            )
        else:
            self.prompts.append(prompt)

    def to_list(self):
        prompts = []
        for p in self.prompts:
            if isinstance(p, McpTool):
                prompts.append({
                    "type": "function_call_output",
                    "call_id": p.call_id,
                    "output": p.function_result,
                })
            elif isinstance(p, PlainInputPrompt):
                prompts.append({
                    'role': p.role, 'content': p.content
                })
            else:
                prompts.append(p)
        return prompts
