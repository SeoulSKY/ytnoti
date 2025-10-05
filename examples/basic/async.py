"""The following example demonstrates how to use the AsyncYouTubeNotifier to listen for
new video uploads from a channel.
"""

import asyncio

from pyngrok import ngrok

from ytnoti import AsyncYouTubeNotifier, Video


async def main() -> None:
    """Run the application."""
    ngrok.set_auth_token("Your ngrok token here")

    notifier = AsyncYouTubeNotifier()

    @notifier.upload()
    async def listener(video: Video) -> None:
        """It is called when a video is uploaded for any channel."""
        print(f"New video from {video.channel.name}: {video.title}")

    await notifier.subscribe("UCuFFtHWoLl5fauMMD5Ww2jA")  # Channel ID of CBC News
    await notifier.run()


if __name__ == "__main__":
    asyncio.run(main())
