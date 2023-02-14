import abc
from pathlib import Path
from typing import Any


class BaseFileWriter(abc.ABC):
    """
    Base FileWriter class to be used as parent for all FileWriter subclasses.
    """

    FOLDER_NAME: str = 'FOLDER_NAME'
    PATH_TO_FILES = Path(__file__).parent.absolute().joinpath(FOLDER_NAME)

    def __init__(self):
        super().__init__()

    @classmethod
    @abc.abstractmethod
    async def write(cls, url: Any, content: str) -> str:
        """
        Write :param content: to file, naming is based on :param url:.
        """
        pass

    @classmethod
    @abc.abstractmethod
    def delete(cls, file_name):
        """
        Delete file by :param file_name:.
        """
        pass

    @classmethod
    @abc.abstractmethod
    def drop_all(cls):
        """
        Delete all files in the folder PATH_TO_FILES.
        """
        pass
