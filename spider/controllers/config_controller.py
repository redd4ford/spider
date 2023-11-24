from argparse import Namespace
from configparser import ConfigParser
import os
from typing import Optional

from spider.controllers.core.loggers import logger
from spider.controllers.core.types import ConfigSections
from spider.db import DatabaseManager


class ConfigController:
    """
    Handles work with the config file.
    """

    DEFAULT_FILE_NAME: str = 'config.ini'

    def __init__(self, config_file_path: str = None):
        if config_file_path:
            self.file_name = config_file_path
        else:
            self.file_name = ConfigController.DEFAULT_FILE_NAME
        if not os.path.exists(self.file_name):
            self.__create_empty_config()
            logger.warning(f'File `{self.file_name}` does not exist, creating it...')

        self.config = ConfigParser()
        self.config.read(self.file_name)

        self.database_manager = DatabaseManager()

        self.db_config = self.config[ConfigSections.DATABASE]
        self.infrastructure_config = self.config[ConfigSections.INFRASTRUCTURE]

    def __create_empty_config(self):
        """
        Create an empty config file with the specified sections.
        """
        with open(self.file_name, 'a') as config_file:
            for section in ConfigSections.all():
                config_file.write(f'[{section}]\n')

    def get_db_config(self, key: str) -> Optional[str]:
        """
        Get value by its :param key: from config's [DATABASE] section.
        """
        return self.db_config.get(key, None)

    def get_infrastructure_config(self, key: str) -> Optional[str]:
        """
        Get value by its :param key: from config's [INFRASTRUCTURE] section.
        """
        return self.infrastructure_config.get(key, None)

    def set_config(self, section: str, key: str, value: str):
        """
        Set :param value: for a :param key: field in the config's :param section:.
        """
        if section not in ConfigSections.all():
            raise ValueError(f'Section `{section}` is not listed in ConfigSections')
        self.config.set(section, key, value)

    def is_config_section_empty(self, section: str) -> bool:
        """
        Check if :param section: in config is empty.
        """
        if section not in ConfigSections.all():
            raise ValueError(f'Section `{section}` is not listed in ConfigSections')
        return len(self.config[section].values()) == 0

    def update(self, args: Namespace):
        """
        Update the default DB login credentials.
        Args:
            :param args: (Namespace) - A set of args used to perform DB connection.
        """
        db_login_args = {
            'type': args.db_type,
            'username': args.db_user,
            'password': args.db_pwd,
            'host': args.db_host,
            'name': args.db_name,
        }

        for name, value in db_login_args.items():
            self.set_config(ConfigSections.DATABASE, name, value)

        self.__update_config_file()

    def __update_config_file(self):
        """
        Overwrite the config file.
        """
        with open(self.file_name, 'w') as config_file:
            self.config.write(config_file)
