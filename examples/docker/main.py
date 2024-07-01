"""
This is a basic script that will be run inside a docker container
"""

import logging

from ytnoti import YouTubeNotifier, Video


def main():
    """
    Main function
    """

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    notifier = YouTubeNotifier()

    @notifier.upload()
    async def listener(video: Video):
        print(f"New video from {video.channel.name}: {video.title}")

    notifier.subscribe("UC9EEyg7QBL-stRX-7hTV3ng")  # Channel ID of SpeedyStyle
    notifier.run()


if __name__ == "__main__":
    main()
