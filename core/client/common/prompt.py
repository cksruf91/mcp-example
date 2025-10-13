from pathlib import Path

import yaml

from common.functional.singleton import Singleton


class PromptManager(metaclass=Singleton):
    _file = Path('.').joinpath('resource').joinpath('prompt.yaml')
    _prompt = yaml.safe_load(_file.open('r'))

    _client = _prompt.get('mcp_client')
    system_prompt = _client.get('system_prompt').get('v1')
