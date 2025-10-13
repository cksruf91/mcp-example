from fastmcp import Client

from common.prompt import PromptManager
from common.utils import get_logger


class CommonService:
    config = {
        "mcpServers": {
            "alpha": {
                "url": "http://localhost:9011/mcp"
            },
            "beta": {
                "url": "http://localhost:9012/mcp"
            },
            "resource": {
                "url": "http://localhost:9013/mcp"
            }
        }
    }

    mcp_servers = Client(config)

    def __init__(self, room_id: str = None):
        self.logger = get_logger(room_id)
        self.prompt_manager = PromptManager()
