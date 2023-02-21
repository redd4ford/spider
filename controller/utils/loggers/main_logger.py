import logging


class CustomLogger(logging.getLoggerClass()):
    """
    Custom logger class to add new level names.
    """

    class Levels:
        DBINFO = 5

    def __init__(self, name, level: int = logging.NOTSET):
        super().__init__(name, level)

        logging.addLevelName(5, "DBINFO")

    def dbinfo(self, message: str, *args, **kwargs):
        if self.isEnabledFor(CustomLogger.Levels.DBINFO):
            self._log(CustomLogger.Levels.DBINFO, message, args, **kwargs)


logging.setLoggerClass(CustomLogger)


class CustomFormatter(logging.Formatter):
    """
    Custom logger formatter to add colors to in-terminal messages.
    """

    GREY = '\x1b[38;20m'
    YELLOW = '\x1b[33;20m'
    CYAN = '\033[36m'
    GREEN = '\033[32m'
    RED = '\x1b[31;20m'
    BOLD_RED = '\x1b[31;1m'
    NO_COLOR = '\x1b[0m'
    FORMAT = '%(name)s | %(message)s'

    FORMATS = {
        logging.DEBUG: GREY + FORMAT + NO_COLOR,
        logging.INFO: GREY + FORMAT + NO_COLOR,
        logging.WARNING: YELLOW + FORMAT + NO_COLOR,
        logging.ERROR: RED + FORMAT + NO_COLOR,
        logging.CRITICAL: BOLD_RED + FORMAT + NO_COLOR,
        CustomLogger.Levels.DBINFO: CYAN + FORMAT + NO_COLOR,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


logger = logging.getLogger('spider')
logger.setLevel(CustomLogger.Levels.DBINFO)

ch = logging.StreamHandler()
ch.setLevel(CustomLogger.Levels.DBINFO)

ch.setFormatter(CustomFormatter())

logger.addHandler(ch)
