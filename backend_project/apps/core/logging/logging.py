import logging
from .logging_handler import DatabaseLogHandler

LOGGING_LEVEL = logging.DEBUG

logger = logging.getLogger('AI_feedback_loop')
logger.setLevel(LOGGING_LEVEL)

db_handler = DatabaseLogHandler()
db_handler.setLevel(LOGGING_LEVEL)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
db_handler.setFormatter(formatter)

logger.addHandler(db_handler)

def get_logger():
    return logger
