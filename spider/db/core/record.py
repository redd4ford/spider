import dataclasses
from typing import (
    Dict,
    List,
    Optional,
)

from typing_extensions import Self


@dataclasses.dataclass
class Record:
    __slots__ = ('url', 'title')

    url: str
    title: Optional[str]


class RecordIterator:
    """
    Record iterator implementation.
    """

    def __init__(self, records: List[Record]):
        self.records = records
        self.current = 0

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> Record:
        if self.current < len(self.records):
            result = self.records[self.current]
            self.current += 1
            return result
        raise StopIteration


class RecordSet:
    """
    Iterable set of records.
    """

    def __init__(self, raw_records: List[Dict[str, str]]):
        if len(raw_records) == 0:
            self.records = []
        else:
            self.records = [
                Record(**raw_record)
                for raw_record in raw_records
            ]

    def __iter__(self) -> RecordIterator:
        return RecordIterator(self.records)
