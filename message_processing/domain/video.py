from typing import NewType
from enum import auto, Enum

VideoId = NewType("VideoId", str)
PlaylistId = NewType("PlaylistId", str)


class VideoStatus(Enum):
    IN_PLAYLIST = auto()
    NOT_IN_PLAYLIST = auto()
    NOT_FOUND = auto()
