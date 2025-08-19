import logging
from config import config

def setup_logger():
    """配置全局日志"""
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('iot_gateway.log')
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logger()