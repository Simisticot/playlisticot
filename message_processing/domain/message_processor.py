from dataclasses import dataclass
from message_processing.domain.video_status_checker import VideoStatusChecker
from message_processing.domain.video_id_scanner import VideoIdScanner
from message_processing.domain.video import VideoId, VideoStatus
from message_processing.domain.message import MessageContent, MessageSignal


@dataclass
class MessageDecision:
    videos_to_add: set[VideoId]
    message_signals: set[MessageSignal]


@dataclass
class MessageAnalyzer:
    vid_checker: VideoStatusChecker
    video_id_scanner: VideoIdScanner

    def analyze_message(self, message_content: MessageContent) -> MessageDecision:
        to_add = set()
        signals = set()

        for video_id in self.video_id_scanner.scan_for_ids(message_content):
            status = self.vid_checker.check_video_status(video_id)
            match status:
                case VideoStatus.NOT_IN_PLAYLIST:
                    to_add.add(video_id)
                    signals.add(MessageSignal.ADDED)
                case VideoStatus.IN_PLAYLIST:
                    signals.add(MessageSignal.REPEAT)
                case VideoStatus.NOT_FOUND:
                    signals.add(MessageSignal.NOT_FOUND)
        return MessageDecision(message_signals=signals, videos_to_add=to_add)
