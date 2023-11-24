from spider.controllers.core.types.abstract_types import AbstractEnumType


class SupportedActions(AbstractEnumType):
    """
    Supported actions for `spider cobweb []` command.
    """

    DROP = 'drop'
    CREATE = 'create'
    COUNT = 'count'
