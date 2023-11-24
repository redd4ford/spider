import pytest

try:
    from spider.controllers import ConfigController
except ImportError:
    import sys
    sys.path.append('../spider')
    from spider.controllers import ConfigController


@pytest.fixture()
def config_controller(tmpdir) -> ConfigController:
    return ConfigController(
        config_file_path=f"{tmpdir}/{ConfigController.DEFAULT_FILE_NAME}"
    )
