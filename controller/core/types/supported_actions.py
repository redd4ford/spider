from controller.core.types.abstract_type import AbstractType


class SupportedActions(AbstractType):
    """
    Supported actions for `spider.py cobweb []` command.
    """

    DROP = 'drop'
    CREATE = 'create'
    COUNT = 'count'
