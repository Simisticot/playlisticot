from message_processing.domain.message import MessageContent, MessageSignal
from message_processing.domain.message_processor import (
    MessageAnalyzer,
    MessageDecision,
)
from message_processing.domain.video import VideoId
from message_processing.domain.video_id_scanner import VideoIdScanner
from message_processing.infra.video_status_checker.never_in_status_checker import (
    NeverInStatusChecker,
)


def test_analyze_message_with_no_ids():
    processor = MessageAnalyzer(
        video_id_scanner=VideoIdScanner(), vid_checker=NeverInStatusChecker()
    )
    assert processor.analyze_message(MessageContent("coucou :)")) == MessageDecision(
        videos_to_add=set(), message_signals=set()
    )


def test_analyze_message_with_not_yet_added_video():
    processor = MessageAnalyzer(
        video_id_scanner=VideoIdScanner(), vid_checker=NeverInStatusChecker()
    )
    assert processor.analyze_message(
        MessageContent("https://www.youtube.com/watch?v=m_OKXtw1-S0")
    ) == MessageDecision(
        videos_to_add={VideoId("m_OKXtw1-S0")}, message_signals={MessageSignal.ADDED}
    )
