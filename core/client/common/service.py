import logging
import sys

from fastmcp import Client

from common.prompt import PromptManager


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
        self.logger = self.get_logger(room_id)
        self.prompt_manager = PromptManager()

    @staticmethod
    def get_logger(room_id: str = None) -> logging.LoggerAdapter:
        logger = logging.getLogger("ClientMCP")
        if not logger.handlers:
            logger.setLevel(logging.DEBUG)
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - [%(room_id)s] - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logging.LoggerAdapter(
            logger, {'room_id': room_id or 'N/A'}
        )
