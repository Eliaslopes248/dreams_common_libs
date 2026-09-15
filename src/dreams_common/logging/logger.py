import logging
import sys
from pathlib import Path


# cache all logger object in hash map
logger_cache = {}

def GetLogger(logger_name: str, log_level: int = logging.INFO) -> logging.Logger:
    """This method will create a named logger object"""
    # return logger object if cached already
    if logger_name in logger_cache:
        return logger_cache.get(logger_name, logging.Logger(logger_name, logging.INFO))

    # create logger object and caching
    logger = logging.Logger(logger_name, level=log_level)

    # add default stdout handler
    AddStdoutHandler(logger=logger)

    # add default file handler

    logger_cache[logger_name] = logger
    return logger

def AddStdoutHandler(
    logger: logging.Logger,
    log_level: int = logging.INFO
) -> None:
    """This method will add a STDOUT handler to logger passed"""
    handler     = logging.StreamHandler(stream=sys.stdout)
    formatter   = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    handler.setLevel(level=log_level)
    logger.addHandler(handler)

def AddFileHandler(
    logger: logging.Logger, 
    file: Path, 
    log_level: int = logging.INFO) -> None:
    """This method will add a log file to the logger passed."""

    # ensure log file exists
    if not file.exists() or not file.is_file():
        logger.warning(f"Log file given does not exist.")
        logger.warning(f"Attempting to create file.")

        # ensure parent directory exists
        try:
            file_parent_dir = file.resolve().parent
            Path(file_parent_dir).mkdir(parents=True, exist_ok=True)

            # create log file
            Path(file).touch(exist_ok=True)
        except Exception as e:
            raise Exception(f"Unable to create log file: {e}.")

    try:
        # ensure file is writable
        with file.open(mode="w") as f:
            pass
    except Exception as e:
        raise Exception(f"Unable to write to log file: {e}.")

    # create and add file handler
    handler     = logging.FileHandler(filename=file)
    formatter   = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
    handler.setFormatter(formatter)

    handler.setLevel(log_level)
    logger.addHandler(handler)