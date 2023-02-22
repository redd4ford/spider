import configparser
import os
from typing import Optional

from controller.core.loggers import logger


class ConfigController:
    """
    Handles work with the config file.
    """

    file_name: str = 'config.ini'

    def __init__(self):
        if not os.path.exists(self.file_name):
            self.__create_db_section()
            logger.warning(f'File `{self.file_name}` does not exist, creating it...')

        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.db_config = self.config['DATABASE']

    def __create_db_section(self):
        """
        Create an empty config file with [DATABASE] section.
        """
        with open(self.file_name, 'a') as config_file:
            config_file.write('[DATABASE]')

    def get_db_config(self, key: str) -> Optional[str]:
        """
        Get value by its :param key: from config's DATABASE section.
        """
        return self.db_config.get(key, None)

    def set_db_config(self, key: str, value: str):
        """
        Set :param value: for a :param key: field in the config's DATABASE section.
        """
        self.config.set('DATABASE', key, value)

    def is_db_config_empty(self) -> bool:
        """
        Check if the DATABASE section in config is empty.
        """
        return len(self.db_config.values()) == 0

    def update(self, args):
        """
        Update the default DB login credentials.
        """
        db_login_args = {
            'type': args.db_type,
            'username': args.db_user,
            'password': args.db_pwd,
            'host': args.db_host,
            'name': args.db_name,
        }

        for name, value in db_login_args.items():
            self.set_db_config(name, value)

        self.__update_config_file()

    def __update_config_file(self):
        """
        Overwrite the config file.
        """
        with open(self.file_name, 'w') as config_file:
            self.config.write(config_file)
