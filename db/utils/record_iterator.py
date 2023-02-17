import dataclasses


@dataclasses.dataclass
class Record:
    url: str = ''
    title: str = ''


class RecordIterator:
    """
    Record iterator implementation.
    """

    def __init__(self, records):
        self.records = records
        self.current = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.current < len(self.records):
            result = self.records[self.current]
            self.current += 1
            return result
        raise StopIteration


class RecordSet:
    """
    Iterable set of records.
    """

    def __init__(self, raw_records):
        if len(raw_records) == 0:
            self.records = []
        else:
            if isinstance(raw_records[0], dict):
                self.records = [
                    Record(**raw_record)
                    for raw_record in raw_records
                ]
            else:
                self.records = [
                    Record(*raw_record)
                    for raw_record in raw_records
                ]

    def __iter__(self):
        return RecordIterator(self.records)
