from typing import Any
from dataclasses import dataclass
from message_processing.domain.video_status_checker import (
    VideoStatusChecker,
)
from message_processing.domain.video import VideoId, PlaylistId, VideoStatus
from googleapiclient.http import HttpError


@dataclass
class YoutubeApiStatusChecker(VideoStatusChecker):
    playlist_id: PlaylistId
    youtube: Any

    def check_video_status(self, video_id: VideoId) -> VideoStatus:
        try:
            response = (
                self.youtube.playlistItems()
                .list(
                    part="id",
                    maxResults=25,
                    playlistId=self.playlist_id,
                    videoId=video_id,
                )
                .execute()
            )
        except HttpError as e:
            if e.status_code == 404:
                return VideoStatus.NOT_FOUND
            else:
                raise
        if len(response["items"]) > 0:
            return VideoStatus.IN_PLAYLIST
        else:
            return VideoStatus.NOT_IN_PLAYLIST
