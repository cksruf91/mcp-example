from fastmcp import Client

from common.prompt import PromptManager


class ServiceClient:
    config = {
        "mcpServers": {
            "alpha": {
                "url": "http://localhost:9011/mcp"
            }
        }
    }

    mcp_servers = Client(config)
    prompt_manager = PromptManager()

    def __init__(self):
        ...
