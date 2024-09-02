Changelog
==========

v2.1.0
------

* From now on, YouTubeNotifier extends AsyncYouTubeNotifier and AsyncYouTubeNotifier extends object. BaseYouTubeNotifier was removed.
* Added (Async)YouTubeNotifier.run_in_background(). It works similar to the run method, but it immediately returns when the notifier is running.
* Added (Async) YouTubeNotifier.unsubscribe(). It unsubscribes the subscribed channel IDs
* From now on, (Async)YouTubeNotifier.subscribe() immediately raises ValueError when the given channel ids are not valid. In the past, it didn't raise error until the notifier started running.
* Improved the speed of verifying channel IDs

Following methods are deprecated and will be removed in version 3.0.0
* AsyncYouTubeNotifier.serve() -> use AsyncYouTubeNotifier.run()
* (Async)YouTubeNotifier.add_listener() -> use either add_any_listener(), add_upload_listener(), or add_edit_listener()

Following decorators are deprecated and will be removed in version 3.0.0
* @(Async)YouTubeNotifier.listener() -> use either @any, @upload or @edit

**Full Changelog**: https://github.com/SeoulSKY/ytnoti/compare/v2.0.1...v2.1.0

v2.0.1
------

* Fixed raising TypeError when a video supports multiple languages.

**Full Changelog**: https://github.com/SeoulSKY/ytnoti/compare/v2.0.0...v2.0.1

v2.0.0
------

Breaking Changes
~~~~~~~~~~~~~~~~

* The following fields in ``Video`` are removed as these are not sent by YouTube in the push notifications:

  * description
  * thumbnail
  * stats

Bug Fixes
~~~~~~~~~

* Fixed YouTubeNotifier.run() and AsyncYouTubeNotifier.serve() raising TypeError when the optional parameter ``app`` wasn't given.
* Fixed (Async)YouTubeNotifier not invoking the event listeners for some YouTube channels.

**Full Changelog**: https://github.com/SeoulSKY/ytnoti/compare/v1.1.2...v2.0.0

v1.1.2
------

* Improved error messages, suggesting possible reasons why they occurred
* ``YouTubeNotifier.run()`` and ``AsyncYouTubeNotifier.serve()`` now raises ``ValueError`` if the registered routes in the given ``FastAPI`` instance conflict with the reserved routes for the notifier.

**Full Changelog**: https://github.com/SeoulSKY/ytnoti/compare/v1.1.1...v1.1.2

v1.1.1
------

* Update the type of `dir_path` of the constructor of ``FileVideoHistory`` from ``Path`` to ``str | PathLike[str]``

**Full Changelog**: https://github.com/SeoulSKY/ytnoti/compare/v1.1.0...v1.1.1

v1.1.0
------

* Add an optional parameter ``host`` to ``YouTubeNotifier.run()`` and ``AsyncYouTubeNotifier.serve()`` to
  specify the host to bind to when running the FastAPI server. Defaults to ``0.0.0.0``

**Full Changelog**: https://github.com/SeoulSKY/ytnoti/compare/v1.0.0...v1.1.0

v1.0.0
------

Breaking Changes
~~~~~~~~~~~~~~~~

* Class ``Notification`` is removed. Instead, the class ``Video`` is passed to the listeners. ``Video`` contains a field ``channel``. Their definitions are moved from ``ytnoti.models.notification.py`` to ``ytnoti.models.video.py``
* Parameter ``cache_size`` for ``YouTubeNotifier`` is removed. Instead, it takes ``video_history`` argument and  the constructor of``InMemoryVideoHistory`` takes ``cache_size``
* Parameter ``endpoint`` is removed from ``YouTubeNotifier.run()``. From now on, the endpoint is extracted from the given ``callback_url``
* ``subscribe()`` now raises ``HTTPError`` defined in this package rather than the one defined in package ``httpx``

Improvements
~~~~~~~~~~~~

* Class ``AsyncYouTubeNotifier`` is added. It's the async version of ``YouTubeNotifier`` that can be run in the existing event loop.
* Abstract class ``VideoHistory`` can be passed to the constructor of ``YouTubeNotifier``. ``InMemoryVideoHistory`` and ``FileVideoHistory`` extends the abstract class. You can also implement your own class that extends ``VideoHistory`` and pass it to the ``YouTubeNotifier``

**Full Changelog**: https://github.com/SeoulSKY/ytnoti/compare/v0.1.2...v1.0.0

v0.1.2
------

* Fix ``YouTubeNotifier.run()`` raising an error when it wasn't called inside the main thread
* Add ``YouTubeNotifier.stop()`` that gracefully stops the running ``YouTubeNotifier``
* Remove the ``/health`` endpoint that was used to check whether the server is accepting requests or not

**Full Changelog**: https://github.com/SeoulSKY/ytnoti/compare/v0.1.1...v0.1.2

v0.1.1
------

* Improved the efficiency of verification of channel IDs (it now uses ``HEAD`` request instead of ``GET``)
* For parameter ``channel_ids`` for all ``YouTubeNotifier``'s methods, it can now also take a singular id with type ``str``.
* Added optional parameters to the constructor of ``YouTubeNotifier``
  * ``password`` - The password to use for verifying push notifications. If not provided, a random password will be generated. Defaults to None
  * ``cache_size``: The number of video IDs to keep in the cache to prevent duplicate notifications. Defaults to 5000
* Added ``created_at`` in ``Channel``

**Full Changelog**: https://github.com/SeoulSKY/ytnoti/compare/v0.1.0...v0.1.1

v0.1.0
------

Initial release