import os
import datetime
import logging


# Create a custom formatter
time_format = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(fmt="%(asctime)s [%(levelname)s] - %(message)s", datefmt=time_format)

# Create a logger and set the custom formatter
logger = logging.getLogger("custom_logger")
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)


def addLog(level: str, text: str) -> None:
    """
    Adds new log.

    :param level: log level (`info`, "debug", "warning", "error", "critical").
    :param text: log text.
    """
    
    now = datetime.datetime.now()
    path = f"logs/{now.year}/{now.month}/{now.day}/"
    filename = path + f"log-{now.hour}.log"

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(filename, "a") as file:
        separator_string = f"\n\n{'='*50}\n\n"
        try:
            file.write(f"{now} [{level.upper()}] - {text}" + separator_string)
        except:
            file.write(f"{now} [{level.upper()}] - {text.encode('utf-8')}" + separator_string)
