import logging
import sys
from pythonjsonlogger import jsonlogger

log_handler = logging.StreamHandler(sys.stdout)
formatter = jsonlogger.JsonFormatter(
    fmt="%(asctime)s %(levelname)s %(name)s %(message)s"
)
log_handler.setFormatter(formatter)

logger = logging.getLogger("jua_ai")
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"jua_ai.{name}")