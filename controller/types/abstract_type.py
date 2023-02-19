import abc
from typing import Tuple


class AbstractType(abc.ABC):
    @classmethod
    def all(cls) -> Tuple:
        return tuple(
            getattr(cls, attribute)
            for attribute in filter(
                lambda attribute: attribute.isupper(), dir(cls)
            )
        )
