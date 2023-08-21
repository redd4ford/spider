import abc
from typing import (
    Any,
    Dict,
    Tuple,
)


class DatabaseImplementationInjector(type):
    """
    This metaclass allows to automatically register all the classes that implement
    the base abstract class. Note: the registry excludes the base class itself.

    Reference:
    https://github.com/faif/python-patterns/blob/master/patterns/behavioral/registry.py
    """

    __REGISTRY: Dict[str, 'DatabaseImplementationInjector'] = {}

    def __new__(cls, name: str, bases: Tuple, attrs: Dict[str, Any]):
        new_cls = type.__new__(cls, name, bases, attrs)

        # do not add the base class to the registry, ONLY store the implementations
        if abc.ABC not in bases:
            implementation_name = getattr(new_cls, 'verbose', '')
            cls.__REGISTRY[implementation_name] = new_cls
        return new_cls

    @classmethod
    def get_registry(cls) -> Dict[str, 'DatabaseImplementationInjector']:
        return cls.__REGISTRY


class BaseDatabaseMeta(abc.ABCMeta, DatabaseImplementationInjector):
    """
    A metaclass used to resolve the metaclass conflict error for BaseDatabase by
    inheriting from both abc.ABCMeta and DatabaseImplementationInjector, which are not
    compatible due to their nature and thus cannot be explicitly added to BaseDatabase.
    """
    pass
