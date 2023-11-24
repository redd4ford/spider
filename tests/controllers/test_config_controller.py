from argparse import Namespace
import os

import pytest

try:
    from spider.controllers import ConfigController
except ImportError:
    import sys
    sys.path.append('../spider')
    from spider.controllers import ConfigController

from spider.controllers.core.types import ConfigSections


class TestConfigController:
    def test_create_empty_config_if_not_exists(self, config_controller):
        assert os.path.exists(config_controller.file_name)
        assert tuple(config_controller.config.sections()) == ConfigSections.all()
        for section in ConfigSections.all():
            assert config_controller.is_config_section_empty(section)
        with pytest.raises(
            ValueError,
            match='Section `UNDEFINED_SECTION` is not listed in ConfigSections'
        ):
            config_controller.is_config_section_empty('UNDEFINED_SECTION')
        assert len(config_controller.db_config) == 0
        assert config_controller.get_db_config('type') is None
        assert len(config_controller.infrastructure_config) == 0
        assert config_controller.get_infrastructure_config('platform') is None

    def test_set_config(self, config_controller):
        config_controller.set_config(ConfigSections.DATABASE, 'type', 'mongodb')
        assert config_controller.get_db_config('type') == 'mongodb'
        with pytest.raises(
            ValueError,
            match=f'Section `UNDEFINED_SECTION` is not listed in ConfigSections'
        ):
            config_controller.set_config('UNDEFINED_SECTION', 'key', 'value')

    def test_can_update_db_config(self, config_controller):
        db_credentials = Namespace(
            db_type='postgresql',
            db_user='postgres',
            db_pwd='postgres',
            db_host='127.0.0.1',
            db_name='postgres'
        )
        config_controller.update(db_credentials)
        assert len(config_controller.db_config) == 5
        assert config_controller.get_db_config('type') == db_credentials.db_type
        assert config_controller.get_db_config('username') == db_credentials.db_user
        assert config_controller.get_db_config('password') == db_credentials.db_pwd
        assert config_controller.get_db_config('host') == db_credentials.db_host
        assert config_controller.get_db_config('name') == db_credentials.db_name

    def test_create_custom_path(self, tmpdir):
        ConfigController.DEFAULT_FILE_NAME = (
            f"{tmpdir}/{ConfigController.DEFAULT_FILE_NAME}"
        )
        config_controller = ConfigController()
        assert config_controller.file_name == ConfigController.DEFAULT_FILE_NAME
