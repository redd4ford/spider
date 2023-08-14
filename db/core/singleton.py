from typing import Dict


class Singleton(type):
    """
    Implementation of Singleton as a metaclass.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Borg:
    """
    Implementation of Singleton behavior using Borg (Monostate) pattern.
    """

    _shared_state: Dict[str, str] = {}

    def __init__(self) -> None:
        self.__dict__ = self._shared_state
