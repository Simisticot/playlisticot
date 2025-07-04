import re
from message_processing.domain.video import VideoId


class VideoIdScanner:
    def scan_for_ids(self, text: str) -> list[VideoId]:
        youtube_re = re.compile(
            r"((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?"
        )
        matches = youtube_re.findall(text)
        return [m[5] for m in matches]
