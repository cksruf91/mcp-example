import sys

from fastmcp import Client

from common.prompt import PromptManager

import logging


class ServiceClient:
    config = {
        "mcpServers": {
            "alpha": {
                "url": "http://localhost:9011/mcp"
            },
            "beta": {
                "url": "http://localhost:9012/mcp"
            }
        }
    }

    mcp_servers = Client(config)

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(logging.StreamHandler(sys.stdout))
        self.prompt_manager = PromptManager()
