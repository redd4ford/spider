import signal
from types import (
    FrameType,
    TracebackType,
)
from typing import Union


class DelayedKeyboardInterrupt:
    """
    A context manager to prevent a critical block of code from being interrupted
    with KeyboardInterrupt.
    """

    def __init__(self):
        self.signal_received = None

    def __enter__(self):
        self.signal_received = False
        self.old_handler = signal.signal(signal.SIGINT, self.handler)

    def handler(self, sig: int, frame: Union[FrameType, None]):
        self.signal_received = (sig, frame)

    def __exit__(self, signal_type, value, traceback: Union[TracebackType, None]):
        signal.signal(signal.SIGINT, self.old_handler)
        if self.signal_received:
            self.old_handler(*self.signal_received)
