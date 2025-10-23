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
    plan_execute_system_prompt = _chat.get('plan_executor').get('system_prompt')
    plan_execute_user_prompt = _chat.get('plan_executor').get('user_prompt_template')

    _langchain = _prompt.get('langchain')
    langchain_task_executor = _langchain.get('task_executor')
    langchain_planner = _langchain.get('planner')
    langchain_replanner = _langchain.get('replanner')
