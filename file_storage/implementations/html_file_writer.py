import os
from pathlib import Path
from typing import Any
import uuid

from aiofile import (
    AIOFile,
    Writer,
)
from yarl import URL

from file_storage.core import BaseFileWriter


class HTMLFileWriter(BaseFileWriter):
    """
    HTML file writer, async implementation.
    """

    FOLDER_NAME = 'html_files'
    PATH_TO_FILES = Path(__file__).parent.absolute().joinpath(FOLDER_NAME)

    @classmethod
    async def write(cls, url: URL, html: str) -> str:
        """
        Write HTML content into a file.
        """
        cls.__create_folder_if_not_exists()

        file_name = cls.__generate_file_name(url)
        path = cls.PATH_TO_FILES.joinpath(file_name)

        async with AIOFile(path, mode='w+') as file:
            writer = Writer(file)
            await writer(html)
        return str(path)

    @classmethod
    def delete(cls, file_name: Any):
        """
        Delete the file by filename.
        """
        file_path = cls.PATH_TO_FILES.joinpath(file_name)
        if os.path.exists(file_path):
            os.remove(cls.PATH_TO_FILES.joinpath(file_name))

    @classmethod
    def drop_all(cls):
        """
        Delete all files in the folder, but not drop the folder itself.
        """
        if cls.__is_folder_exists():
            files = os.listdir(cls.PATH_TO_FILES)
            for file in files:
                cls.delete(file)

    @classmethod
    def __generate_file_name(cls, url: URL) -> str:
        """
        Format: `subdomain_link_uuid4.html`, e.g. www_google_com_<UUID4>.html
        """
        return f'{url.host.replace(".", "_")}_{uuid.uuid4()}.html'

    @classmethod
    def __is_folder_exists(cls) -> bool:
        return os.path.exists(cls.PATH_TO_FILES)

    @classmethod
    def __create_folder_if_not_exists(cls):
        if not cls.__is_folder_exists():
            os.makedirs(cls.PATH_TO_FILES)
