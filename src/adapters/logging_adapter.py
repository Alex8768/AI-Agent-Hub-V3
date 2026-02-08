"""
Loguru Adapter (Synchronous)
"""
import sys
from typing import Optional, Dict, Any
from loguru import logger as loguru_logger

# Простой wrapper, чтобы не менять весь код проекта
class SyncLogger:
    def __init__(self):
        self._logger = loguru_logger
        self._logger.remove()
        self._logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>", level="INFO")

    def info(self, msg: str, **kwargs):
        self._logger.info(msg, **kwargs)
    
    def error(self, msg: str, **kwargs):
        self._logger.error(msg, **kwargs)
    
    def warning(self, msg: str, **kwargs):
        self._logger.warning(msg, **kwargs)
    
    def debug(self, msg: str, **kwargs):
        self._logger.debug(msg, **kwargs)

_global_logger = SyncLogger()

def get_logger():
    return _global_logger
