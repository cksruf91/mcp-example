from pathlib import Path

import yaml

from common.functional.singleton import Singleton


class PromptManager(metaclass=Singleton):
    _file = Path('.').joinpath('resource').joinpath('prompt.yaml')
    _prompt = yaml.safe_load(_file.open('r')).get('mcp_client')

    _chat = _prompt.get('chat')
    system_prompt = _chat.get('system_prompt').get('v1')

    _chat = _prompt.get('pne')
    planning_instruction_prompt = _chat.get('planning_instruction_prompt').get('v3')
    replanning_prompt = _chat.get('replanning_prompt').get('v2')
