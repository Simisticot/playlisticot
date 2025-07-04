from message_processing.domain.video import VideoStatus, VideoId
from message_processing.domain.video_status_checker import VideoStatusChecker


class NeverInStatusChecker(VideoStatusChecker):
    def check_video_status(self, video_id: VideoId) -> VideoStatus:
        return VideoStatus.NOT_IN_PLAYLIST
