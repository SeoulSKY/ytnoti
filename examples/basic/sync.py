"""This example demonstrates how to use the YouTubeNotifier to listen for new video
uploads from a channel.
"""

from pyngrok import ngrok

from ytnoti import YouTubeNotifier, Video


def main():
    """Main function"""

    ngrok.set_auth_token("Your ngrok token here")

    notifier = YouTubeNotifier()

    @notifier.upload()
    async def listener(video: Video):
        print(f"New video from {video.channel.name}: {video.title}")

    notifier.subscribe("UC9EEyg7QBL-stRX-7hTV3ng")  # Channel ID of SpeedyStyle
    notifier.run()


if __name__ == "__main__":
    main()
