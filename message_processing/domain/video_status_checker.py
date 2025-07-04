from typing import Protocol
from abc import abstractmethod
from message_processing.domain.video import VideoStatus, VideoId


class VideoStatusChecker(Protocol):
    @abstractmethod
    def check_video_status(self, video_id: VideoId) -> VideoStatus: ...
