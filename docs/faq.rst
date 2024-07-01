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

Their usage is very similar, except that the AsyncYouTubeNotifier has ``serve()`` method instead of ``run()`` method.
Following are the differences between them:

YouTubeNotifier
~~~~~~~~~~~~~~~
* Public methods are synchronous.
* ``run()`` method can be run in a sub-thread.
* Creates a new asyncio event loop and runs the notifier in it.

AsyncYouTubeNotifier
~~~~~~~~~~~~~~~~~~~~
* Public methods are asynchronous.
* ``serve()`` method can only be run in the main thread.
* Serves in the existing asyncio event loop.

To see the difference in usage between them,
see the `sync.py <https://github.com/SeoulSKY/ytnoti/tree/main/examples/basic/sync.py>`_ and
`async.py <https://github.com/SeoulSKY/ytnoti/tree/main/examples/basic/async.py>`_ examples.
