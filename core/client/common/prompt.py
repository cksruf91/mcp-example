from pathlib import Path

import yaml

from common.functional.singleton import Singleton


class PromptManager(metaclass=Singleton):
    _file = Path('.').joinpath('resource').joinpath('prompt.yaml')
    _prompt = yaml.safe_load(_file.open('r'))

    _v1 = _prompt.get('mcp_client').get('v1')
    system_prompt = _v1.get('system_prompt')
