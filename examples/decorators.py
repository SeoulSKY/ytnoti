"""The following is an example of how to use decorators to listen to notifications."""

from pyngrok import ngrok

from ytnoti import DeletedVideo, Video, YouTubeNotifier


def main() -> None:
    """Run the application."""
    ngrok.set_auth_token("Your ngrok token here")

    notifier = YouTubeNotifier()

    @notifier.any()
    async def listener1(video: Video | DeletedVideo) -> None:
        """Listener called when a video is uploaded, deleted, or edited for
        any channel.
        """
        print("listener 1 called")
        print(video)

    @notifier.upload()
    async def listener2(video: Video) -> None:
        """Listener called when a video is uploaded for any channel."""
        print("listener 2 called")
        print(video)

    @notifier.upload(channel_ids="UCupvZG-5ko_eiXAupbDfxWw")
    @notifier.edit()
    async def listener3(video: Video) -> None:
        """Listener called when a video is uploaded on a specific channel and when a
        video is edited on any channel.
        """
        print("listener 3 called")
        print(video)

    @notifier.delete()
    async def listener4(video: DeletedVideo) -> None:
        """Listener called when a video is deleted for any channel."""
        print("listener 4 called")
        print(video)

    notifier.subscribe(["UCupvZG-5ko_eiXAupbDfxWw", "UChLtXXpo4Ge1ReTEboVvTDg"])
    notifier.run()


if __name__ == "__main__":
    main()
