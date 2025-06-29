# This example requires the 'message_content' intent.

import json
import re
import googleapiclient.discovery
import google.oauth2.credentials
import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True


CREDS = google.oauth2.credentials.Credentials(
    **json.loads(open("creds.json", "r").read())
)

watched_channels: set[int] = set()

bot = commands.Bot(command_prefix="$", intents=intents)

youtube_re = re.compile(
    r"((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?"
)


@bot.event
async def on_ready():
    print(f"logged in as {bot.user}")


@bot.event
async def on_message(message: discord.Message):
    if message.content.startswith("$"):
        await bot.process_commands(message)
    if message.author.id == bot.user.id:
        print("message from self")
    if message.guild is None:
        print("invalid channel")
        return
    if message.guild.id not in watched_channels:
        print("not a watched channel")
        return
    matches = youtube_re.findall(message.content)
    if len(matches) == 0:
        print("no matches")
        return
    else:
        youtube = googleapiclient.discovery.build("youtube", "v3", credentials=CREDS)
        for m in matches:
            youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": "PLVKgx_siHkYG6eRYnnvUlZzWIURV5qeJH",
                        "position": 0,
                        "resourceId": {"kind": "youtube#video", "videoId": m[5]},
                    }
                },
            ).execute()
            await message.channel.send(f"added {m[5]} to the playlist")


@bot.command()
async def watch(ctx: commands.Context):
    if ctx.guild is None:
        await ctx.send("this isn't a channel I can watch")
        return
    channel_id = ctx.guild.id
    watched_channels.add(channel_id)
    await ctx.send(f"watching channel {channel_id}")


@bot.command()
async def watched(ctx: commands.Context):
    await ctx.send(
        f"watched channels: {", ".join(str(channel) for channel in watched_channels)}"
    )


@bot.command()
async def add(ctx: commands.Context, id: str):
    await ctx.send(f"adding video {id}")
    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=CREDS)
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
