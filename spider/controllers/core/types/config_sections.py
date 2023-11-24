from spider.controllers.core.types.abstract_types import AbstractEnumType


class ConfigSections(AbstractEnumType):
    """
    Sections in `config.ini` file.
    """

    DATABASE = 'DATABASE'
    INFRASTRUCTURE = 'INFRASTRUCTURE'
