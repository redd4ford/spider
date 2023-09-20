from typing import (
    Any,
    Dict,
)

from typing_extensions import Self


class Borg:
    """
    Implementation of Singleton behavior using Borg (Monostate) pattern.
    """

    _shared_state: Dict[str, Any] = {}

    def __init__(self) -> None:
        self.__dict__ = self._shared_state

    def __hash__(self):
        return 1

    def __eq__(self, other: Self) -> bool:
        try:
            return isinstance(other, type(self)) and self.__dict__ is other.__dict__
        except AttributeError:
            return False
