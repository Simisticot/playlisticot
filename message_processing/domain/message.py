from enum import auto, Enum
from typing import NewType
from dataclasses import dataclass
from message_processing.domain.video import VideoId

MessageContent = NewType("MessageContent", str)


class MessageSignal(Enum):
    ADDED = auto()
    NOT_FOUND = auto()
    REPEAT = auto()
