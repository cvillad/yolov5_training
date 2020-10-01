import logging

info_level = logging.INFO
debug_level = logging.DEBUG
warning_level = logging.WARNING
error_level = logging.ERROR

def get_logger(level=logging.INFO):
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=level)
    logger = logging.getLogger()
    return logger