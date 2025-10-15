import logging


def get_logger(room_id: str = None) -> logging.LoggerAdapter:
    logger = logging.getLogger("ClientMCP")
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - [%(room_id)s] - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logging.LoggerAdapter(
        logger, {'room_id': room_id or 'N/A'}
    )
