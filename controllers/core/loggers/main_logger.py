import logging


class CustomLogger(logging.getLoggerClass()):
    """
    Custom logger class to add new level names.
    """

    class Levels:
        """
        Level hierarchy from :package logging: is commented out
        to understand where custom levels are located at.
        """
        # logging.DEBUG: 10
        DB_INFO = 11
        CRAWL_ONGOING_INFO = 13
        CRAWL_SUCCESS = 15
        # a few more levels can be added here...
        # logging.INFO: 20
        # logging.WARNING, logging.WARN: 30
        # logging.ERROR: 40
        # logging.CRITICAL, logging.FATAL: 50

    def __init__(self, name, level: int = logging.NOTSET):
        super().__init__(name, level)

        logging.addLevelName(CustomLogger.Levels.DB_INFO, "DB_INFO")
        logging.addLevelName(CustomLogger.Levels.CRAWL_ONGOING_INFO, "CRAWL_INFO")
        logging.addLevelName(CustomLogger.Levels.CRAWL_SUCCESS, "CRAWL_SUCCESS")

    def db_info(self, message: str, *args, **kwargs):
        level = CustomLogger.Levels.DB_INFO

        if self.isEnabledFor(level):
            self._log(level, message, args, **kwargs)

    def crawl_info(self, message: str, *args, **kwargs):
        level = CustomLogger.Levels.CRAWL_ONGOING_INFO

        if self.isEnabledFor(level):
            self._log(level, message, args, **kwargs)

    def crawl_ok(self, message: str, *args, **kwargs):
        level = CustomLogger.Levels.CRAWL_SUCCESS

        if self.isEnabledFor(level):
            self._log(level, message, args, **kwargs)

    def update_level(self, silent: bool, operation: str):
        log_level = 0
        if operation == 'crawl':
            log_level = self.get_level_for_crawl(silent)
        elif operation == 'db':
            log_level = self.get_level_for_db(silent)
        self.setLevel(log_level)
        self.__update_handlers_level(log_level)

    @classmethod
    def get_level_for_crawl(cls, silent: bool) -> int:
        return (
            CustomLogger.Levels.CRAWL_SUCCESS
            if silent
            else
            CustomLogger.Levels.CRAWL_ONGOING_INFO
        )

    @classmethod
    def get_level_for_db(cls, silent: bool) -> int:
        return (
            logging.INFO
            if silent
            else
            CustomLogger.Levels.DB_INFO
        )

    def __update_handlers_level(self, log_level: int):
        for one_handler in self.handlers:
            one_handler.setLevel(log_level)


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
    FORMAT = '%(name)s 🕸 %(message)s'

    FORMATS = {
        logging.DEBUG: GREY + FORMAT + NO_COLOR,
        CustomLogger.Levels.DB_INFO: CYAN + FORMAT + NO_COLOR,
        CustomLogger.Levels.CRAWL_ONGOING_INFO: YELLOW + FORMAT + NO_COLOR,
        CustomLogger.Levels.CRAWL_SUCCESS: GREEN + FORMAT + NO_COLOR,
        logging.INFO: GREY + FORMAT + NO_COLOR,
        logging.WARNING: YELLOW + FORMAT + NO_COLOR,
        logging.ERROR: RED + FORMAT + NO_COLOR,
        logging.CRITICAL: BOLD_RED + FORMAT + NO_COLOR,
    }

    def format(self, record: logging.LogRecord) -> str:
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


logger = logging.getLogger('spider')
logger.setLevel(CustomLogger.Levels.DB_INFO)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(CustomLogger.Levels.DB_INFO)
stream_handler.setFormatter(CustomFormatter())

logger.addHandler(stream_handler)
