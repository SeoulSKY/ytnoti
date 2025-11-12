"""Script for end-to-end testing the YouTubeNotifier."""

import logging
import os

from dotenv import load_dotenv
from pyngrok import ngrok

from ytnoti import Video, YouTubeNotifier

if __name__ == "__main__":  # pragma: no cover
    load_dotenv()
    ngrok.set_auth_token(os.environ["NGROK_TOKEN"])

    notifier = YouTubeNotifier()

    @notifier.upload()
    async def _(video: Video) -> None:
        print(f"New video from {video.channel.name}: {video.title}")  # noqa: T201

    notifier.subscribe("UCupvZG-5ko_eiXAupbDfxWw")  # Channel ID of CNN
    logging.basicConfig(level=logging.INFO)
    notifier.run()
