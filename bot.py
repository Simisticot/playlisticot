# This example requires the 'message_content' intent.

import json
import re
import googleapiclient.discovery
import google.oauth2.credentials
import discord
from discord.ext import commands
import os
from time import sleep

from googleapiclient.http import HttpError

intents = discord.Intents.default()
intents.message_content = True


CREDS = google.oauth2.credentials.Credentials(
    **json.loads(open("creds.json", "r").read())
)
youtube = googleapiclient.discovery.build("youtube", "v3", credentials=CREDS)

watched_channels: dict[int, str] = dict()

bot = commands.Bot(command_prefix="$", intents=intents)

youtube_re = re.compile(
    r"((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?"
)


def should_add_video(youtube, vid_id: str, playlist_id: str) -> bool:
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
            return False
        else:
            raise
    return not len(response["items"]) > 0


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
    matches = youtube_re.findall(message.content)
    if len(matches) == 0:
        print("no matches")
        return
    else:
        playlist_id = watched_channels.get(message.channel.id)
        if playlist_id is None:
            await message.channel.send("couldn't find playlist :(")
        else:
            for m in matches:
                if not should_add_video(youtube, m[5], playlist_id):
                    await message.channel.send("this video is already in the list")
                else:
                    add_video_to_playlist(youtube, m[5], playlist_id)
                    await message.channel.send(f"added {m[5]} to the playlist")


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
        watched_channels[channel_id] = response["id"]

        await ctx.send(
            f"watching channel {channel_id}, created playlist, catching up.."
        )

        added = 0
        skipped = 0
        already_in = set()
        async for message in ctx.channel.history():
            matches = youtube_re.findall(message.content)
            for m in matches:
                sleep(0.5)
                print(f"handling video {m[5]}")
                if not (
                    m[5] in already_in
                    or not should_add_video(youtube, m[5], response["id"])
                ):
                    add_video_to_playlist(youtube, m[5], response["id"])
                    added += 1
                else:
                    already_in.add(m[5])
                    skipped += 1
        await ctx.send(f"all caught up, added {added} videos, skipped {skipped}")


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
