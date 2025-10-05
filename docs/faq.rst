Frequently Asked Questions
==========================

Why is ngrok used in this package?
----------------------------------

ngrok is used to expose the local server to the internet.
This is necessary because the webhook URL must be accessible from the internet.
If you don't provide ``callback_url`` to the constructor of the ``YouTubeNotifier`` or ``AsyncYouTubeNotifier``,
the notifier will use ngrok to expose the local server to the internet.
It's useful for development purposes.

What are the differences between YoutubeNotifier and AsyncYoutubeNotifier?
--------------------------------------------------------------------------

Their usage is very similar, except for the followings:

YouTubeNotifier
~~~~~~~~~~~~~~~
* Public methods are synchronous.
* ``run()`` method can be run in a sub-thread.
* Creates a new asyncio event loop and runs the notifier in it.

AsyncYouTubeNotifier
~~~~~~~~~~~~~~~~~~~~
* Public methods are asynchronous.
* ``run()`` method can only be run in the main thread.
* Runs in the existing asyncio event loop.

To see the difference in usage between them,
see the `sync.py <https://github.com/SeoulSKY/ytnoti/tree/main/examples/basic/sync.py>`_ and
`async.py <https://github.com/SeoulSKY/ytnoti/tree/main/examples/basic/async.py>`_ examples.

Why does the update listeners sometimes get trigger even when a video was edited?
-------------------------------------------------------------------------------------

This can occur due to limitations in the information provided by the YouTube webhook. Specifically, the webhook does not indicate whether a video is newly uploaded or merely edited.

By default, the library keeps track of video IDs in memory to identify uploaded videos. If a video ID is already in memory, the library will trigger the edit listeners.

As a result, if you restart your program, previously uploaded videos are no longer in memory. When the webhook notifies your application, it may incorrectly trigger an upload event even for edited videos.

To maintain persistent memory of video IDs across restarts, provide an instance of ``FileVideoHistory`` to the constructor of ``(Async)YoutubeNotifier``.
