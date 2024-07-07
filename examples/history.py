"""
This example demonstrates how to use the FileVideoHistory class to keep track of the videos that have been
uploaded or edited. This class stores the video history in a file on the local disk. This is useful when you want to
keep track of the videos that have been uploaded or edited, even if the program is restarted.

You can also extend the abstract class VideoHistory to create your own custom video history storage.
"""

from pyngrok import ngrok

from ytnoti import YouTubeNotifier, Video
from ytnoti.models.history import FileVideoHistory


def main():
    """
    Main function
    """

    ngrok.set_auth_token("Your ngrok token here")

    # This will create a new folder called "videoHistory" in the current directory
    video_history = FileVideoHistory(dir_path="./videoHistory")

    notifier = YouTubeNotifier(video_history=video_history)

    @notifier.upload()
    async def listener(video: Video):
        print(f"New video from {video.channel.name}: {video.title}")

    notifier.subscribe("UCupvZG-5ko_eiXAupbDfxWw")
    notifier.run()


if __name__ == "__main__":
    main()
