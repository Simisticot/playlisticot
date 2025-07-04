# This example requires the 'message_content' intent.

from dataclasses import dataclass
from enum import Enum, auto
import json
import re
import googleapiclient.discovery
import google.oauth2.credentials
import discord
from discord.ext import commands
import os
from time import sleep
from typing import Callable

from googleapiclient.http import HttpError
from message_processing.domain.message import MessageContent, MessageSignal
from message_processing.domain.message_processor import MessageAnalyzer
from message_processing.domain.video import PlaylistId
from message_processing.domain.video_id_scanner import VideoIdScanner
from message_processing.infra.video_status_checker.youtube_api_status_checker import (
    YoutubeApiStatusChecker,
)

intents = discord.Intents.default()
intents.message_content = True


CREDS = google.oauth2.credentials.Credentials(
    **json.loads(open("creds.json", "r").read())
)
youtube = googleapiclient.discovery.build("youtube", "v3", credentials=CREDS)

watched_channels: dict[int, str] = dict()

bot = commands.Bot(command_prefix="$", intents=intents)


@dataclass
class AddToPlaylist:
    video_id: str


class VideoStatus(Enum):
    IN_PLAYLIST = auto()
    NOT_IN_PLAYLIST = auto()
    DOES_NOT_EXIST = auto()


def analyzer_factory(playlist_id: PlaylistId, youtube) -> MessageAnalyzer:
    checker = YoutubeApiStatusChecker(playlist_id=playlist_id, youtube=youtube)
    scanner = VideoIdScanner()
    return MessageAnalyzer(video_id_scanner=scanner, vid_checker=checker)


def handle_message(
    message_content: str,
    video_status: Callable[[str], VideoStatus],
    find_ids: Callable[[str], list[str]],
) -> list[AddToPlaylist]:
    to_add: list[AddToPlaylist] = []
    for id in find_ids(message_content):
        if video_status(id) == VideoStatus.IN_PLAYLIST:
            to_add.append(AddToPlaylist(video_id=id))
    return to_add


def find_video_ids(text: str) -> list[str]:
    youtube_re = re.compile(
        r"((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?"
    )
    matches = youtube_re.findall(text)
    return [m[5] for m in matches]


def check_video_status(youtube, vid_id: str, playlist_id: str) -> VideoStatus:
    try:
        response = (
            youtube.playlistItems()
            .list(
                part="id",
                maxResults=25,
                playlistId=playlist_id,
                videoId=vid_id,
            )
            .execute()
        )
    except HttpError as e:
        if e.status_code == 404:
            return VideoStatus.DOES_NOT_EXIST
        else:
            raise
    if len(response["items"]) > 0:
        return VideoStatus.IN_PLAYLIST
    else:
        return VideoStatus.NOT_IN_PLAYLIST


def add_video_to_playlist(youtube, vid_id: str, playlist_id: str) -> None:
    youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "position": 0,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": vid_id,
                },
            }
        },
    ).execute()


def handle_add_actions(actions: list[AddToPlaylist], playlist_id: str) -> None:
    for action in actions:
        add_video_to_playlist(youtube, action.video_id, playlist_id)


@bot.event
async def on_ready():
    print(f"logged in as {bot.user}")


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    print(error)
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing required argument :(")


@bot.event
async def on_message(message: discord.Message):
    if message.content.startswith("$"):
        await bot.process_commands(message)
    if message.author.id == bot.user.id:
        print("message from self")
    if message.channel.id is None:
        print("invalid channel")
        return
    if message.channel.id not in watched_channels:
        print("not a watched channel")
        return
    playlist_id = watched_channels.get(message.channel.id)
    if playlist_id is None:
        await message.channel.send("couldn't find playlist :(")
        return
    analyzer = analyzer_factory(playlist_id=PlaylistId(playlist_id), youtube=youtube)
    decision = analyzer.analyze_message(MessageContent(message.content))
    for vid_id in decision.videos_to_add:
        add_video_to_playlist(youtube=youtube, playlist_id=playlist_id, vid_id=vid_id)
        print(decision.message_signals)
        if MessageSignal.ADDED in decision.message_signals:
            await message.add_reaction("✅")
        if MessageSignal.REPEAT in decision.message_signals:
            await message.add_reaction("🔁")
        if MessageSignal.NOT_FOUND in decision.message_signals:
            await message.add_reaction("❓")


@bot.command()
async def watch(
    ctx: commands.Context,
    title: str,
):
    if not title:
        await ctx.send("title please :(")
    channel_id = ctx.channel.id
    if channel_id is None:
        await ctx.send("can't find the channel")
    if channel_id in watched_channels:
        await ctx.send("this channel is already watched")

    response = (
        youtube.playlists()
        .insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                },
                "status": {"privacyStatus": "public"},
            },
        )
        .execute()
    )
    if "id" not in response:
        print(response)
    else:
        playlist_id = PlaylistId(response["id"])
        watched_channels[channel_id] = response["id"]

        await ctx.send(
            f"watching channel {channel_id}, created playlist, catching up.."
        )

        analyzer = analyzer_factory(
            playlist_id=PlaylistId(playlist_id), youtube=youtube
        )
        added = 0
        async for message in ctx.channel.history():
            decision = analyzer.analyze_message(MessageContent(message.content))
            for vid_id in decision.videos_to_add:
                add_video_to_playlist(
                    youtube=youtube, playlist_id=playlist_id, vid_id=vid_id
                )
            print(decision.message_signals)
            if MessageSignal.ADDED in decision.message_signals:
                await message.add_reaction("✅")
            if MessageSignal.REPEAT in decision.message_signals:
                await message.add_reaction("🔁")
            if MessageSignal.NOT_FOUND in decision.message_signals:
                await message.add_reaction("❓")
            added += len(decision.videos_to_add)
        await ctx.send(f"all caught up, added {added} videos")


@bot.command()
async def watched(ctx: commands.Context):
    await ctx.send(
        f"watched channels: {", ".join(str(channel) for channel in watched_channels)}"
    )


@bot.command()
async def add(ctx: commands.Context, id: str):
    await ctx.send(f"adding video {id}")
    youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": "PLVKgx_siHkYG6eRYnnvUlZzWIURV5qeJH",
                "position": 0,
                "resourceId": {"kind": "youtube#video", "videoId": id},
            }
        },
    ).execute()
    await ctx.send("Done !")


@bot.command()
async def rename(ctx: commands.Context, name: str):
    await ctx.send(f"renaming to {name}")
    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=CREDS)
    youtube.playlists().update(
        part="snippet,status",
        body={
            "id": "PLVKgx_siHkYG6eRYnnvUlZzWIURV5qeJH",
            "snippet": {
                "title": name,
            },
        },
    ).execute()


token = os.environ.get("DISCORD_TOKEN")
if token is None:
    print("Please provide a discord token in environment variable 'DISCORD_TOKEN'")
else:
    bot.run(token)
