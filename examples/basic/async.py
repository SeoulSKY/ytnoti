"""
This example demonstrates how to use the AsyncYouTubeNotifier to listen for new video uploads from a channel.
"""

import asyncio

from ytnoti import AsyncYouTubeNotifier, Video


async def main():
    """
    Main function
    """

    notifier = AsyncYouTubeNotifier()

    @notifier.upload()
    async def listener(video: Video):
        """
        Listener called when a video is uploaded for any channel
        """

        print(f"New video from {video.channel.name}: {video.title}")

    await notifier.subscribe("UC9EEyg7QBL-stRX-7hTV3ng")  # Channel ID of SpeedyStyle
    await notifier.serve()


if __name__ == "__main__":
    asyncio.run(main())
