"""
This example demonstrates how to use this library with discord.py
"""

import logging

import discord
from discord import TextChannel

from ytnoti import AsyncYouTubeNotifier
from ytnoti.models.notification import Notification


class MyClient(discord.Client):
    """
    Custom discord client for methods overriding
    """

    def __init__(self):
        """
        Create a new instance of the client
        """

        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(intents=intents)

        self._notifier = AsyncYouTubeNotifier()
        self._listeners: dict[str, list[TextChannel]] = {}

        async def listener(notification: Notification) -> None:
            """
            Listener called when a video is uploaded
            """

            channels = self._listeners[notification.channel.id]
            for channel in channels:
                await channel.send(f"{notification.channel.name} uploaded a [new video]({notification.video.url})")

        self._notifier.add_upload_listener(listener)

    async def on_ready(self) -> None:
        """
        Called when the client is ready
        """

        print("Logged on as", self.user)

        await self._notifier.serve()

    async def on_message(self, message: discord.Message) -> None:
        """
        Called when a message is received
        """

        if not message.content.startswith("!subscribe"):
            return

        async with message.channel.typing():
            args = message.content.split(" ")[1:]

            if len(args) < 1:
                await message.reply("Usage: !subscribe <channel_id>")
                return

            channel_id = args[0].strip()

            try:
                await self._notifier.subscribe(channel_id)
            except ValueError:
                await message.reply(f"Invalid channel ID: {channel_id}")
                return

            if channel_id not in self._listeners:
                self._listeners[channel_id] = []

            self._listeners[channel_id].append(message.channel)

            await message.reply(f"Subscribed to the channel: {channel_id}")


if __name__ == "__main__":
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_LEVEL = logging.DEBUG
    logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)

    client = MyClient()
    client.run("token", log_formatter=logging.Formatter(LOG_FORMAT), log_level=LOG_LEVEL)
