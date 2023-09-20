import abc
from typing import Tuple


class AbstractEnumType(abc.ABC):
    @classmethod
    def all(cls) -> Tuple:
        """
        Return all type fields that are in uppercase.
        """
        return tuple(
            getattr(cls, attribute)
            for attribute in filter(
                lambda attribute: attribute.isupper(), dir(cls)
            )
        )
