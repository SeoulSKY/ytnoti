Changelog
==========

v3.0.4
------

Fixes
~~~~~

* Fix that a newly uploaded video was often reported as an edit instead of an upload, so the upload listeners never ran for it. Whether a video is new is now decided by whether (Async)YouTubeNotifier has already seen it, rather than by how far apart YouTube set its published and updated times, which for a new video are routinely minutes apart.
* Fix that only the videos reported as uploads were recorded in the ``VideoHistory``, which let the hub resending the same video be reported as an upload again. Every video is now recorded the first time it is seen.
* Fix that ``FileVideoHistory`` appended a video to its file every time it was added, so repeatedly adding the same video pushed the other videos out and made the history hold fewer of them than ``num_videos``. Adding a video it already holds now has no effect, as it already did for ``InMemoryVideoHistory``.
* Fix that (Async)YouTubeNotifier said nothing while it waited for its callback URL to become reachable on startup, so a callback URL that was never going to answer was indistinguishable from a notifier that had hung. Every failed attempt is now logged, and the URL is checked twice a second instead of ten times a second. Thanks to `@hoshinolina <https://github.com/hoshinolina>`__ for `#10 <https://github.com/SeoulSKY/ytnoti/pull/10>`__!
* Fix that ``subscribe`` rejected a valid channel ID with ``ValueError`` whenever YouTube's video feed for that channel answered with an error, which it had started doing at random. Channel IDs are now checked against the channel's page instead. Thanks to `@hoshinolina <https://github.com/hoshinolina>`__ for `#9 <https://github.com/SeoulSKY/ytnoti/pull/9>`__!
* Fix that a subscription was reported as successful even when the hub never called back to verify it, which left the channel without notifications. It now counts as a failure: it is retried, and ``subscribe`` raises ``SubscribeError``. Thanks to `@hoshinolina <https://github.com/hoshinolina>`__ for `#11 <https://github.com/SeoulSKY/ytnoti/pull/11>`__!
* Fix that every subscription was renewed once a day no matter how long the hub had granted it for, and that a failed renewal requested every channel again. Each channel is now renewed once 70 to 80 percent of the lease the hub actually granted has passed, and a retry requests only the channels that failed. Thanks to `@hoshinolina <https://github.com/hoshinolina>`__ for `#11 <https://github.com/SeoulSKY/ytnoti/pull/11>`__!
* Request the longest lease the hub allows, 10 days instead of its default of 5, so that a subscription outlasts a longer outage of the hub before it runs out. Thanks to `@hoshinolina <https://github.com/hoshinolina>`__ for `#13 <https://github.com/SeoulSKY/ytnoti/pull/13>`__!
* Wait 2 minutes instead of 1 before the first retry of a failed subscription, which is the interval the hub asks for when it is overloaded. Thanks to `@hoshinolina <https://github.com/hoshinolina>`__ for `#11 <https://github.com/SeoulSKY/ytnoti/pull/11>`__!
* Fix that (Async)YouTubeNotifier stopped checking its callback URL on startup when the connection was reset or closed, rather than refused, so it never became ready and ``run_in_background`` never returned. Every connection error is now retried.
* Fix that ``AsyncYouTubeNotifier.run_in_background`` waited forever when the server failed to start. It now raises the server's error, or a ``RuntimeError`` if the server stopped before it was ready without one.

**Full Changelog**: https://github.com/SeoulSKY/ytnoti/compare/v3.0.3...v3.0.4

v3.0.3
------

Fixes
~~~~~

* Fix that a failed subscription right after the notifier started left it running without ever subscribing again, so no notification ever arrived. It's now retried with the same exponential backoff as the daily resubscription.

**Full Changelog**: https://github.com/SeoulSKY/ytnoti/compare/v3.0.2...v3.0.3

v3.0.2
------

Fixes
~~~~~

* Fix that the requests to YouTube timed out after 5 seconds, which was often too short for a subscription request. They now time out after 30 seconds.
* Fix that a single failing channel prevented the remaining channels from being subscribed or unsubscribed. Every channel is now requested, and the first error is raised once all of them are done.
* Fix that a failed daily resubscription waited for a full day before being retried. It's now retried with an exponential backoff that starts at a minute.
* Keep a reference to the task created when the notifier starts, so that it can't be garbage collected while running.

**Full Changelog**: https://github.com/SeoulSKY/ytnoti/compare/v3.0.1...v3.0.2

v3.0.1
------

Fixes
~~~~~

* Fix that ``(Async)YouTubeNotifier`` didn't work properly with Starlette 1.0.

**Full Changelog**: https://github.com/SeoulSKY/ytnoti/compare/v3.0.0...v3.0.1

v3.0.0
------

Features
~~~~~~~~

* ``(Async)YouTubeNotifier`` can now receive delete events from YouTube. Add a listener by using ``@notifier.delete()`` decorator.
* ``@notifier.any()`` now receives an either ``Video`` or ``DeletedVideo`` object as an argument, since it now also receives delete events.

Fixes and Deprecations
~~~~~~~~~~~~~~~~~~~~~~

* Fix that the passed ``port`` keyword argument to ``(Async)YouTubeNotifier.run()`` was ignored when ngrok tunnel was used.
* Deprecate ``app`` keyword argument for ``(Async)YouTubeNotifier.run()``. It will be removed in version 4.0.0. Pass the ``FastAPI`` instance to the constructor instead.
* Send an unsubscribe request to YouTube when the notification was for the channel that is not subscribed anymore.
* Stopping the notifier no longer sends unsubscribe requests.
* Improve the event classification logic. It now also checks the timestamp of the video in addition to video history to determine if the event is a new upload or an edit.
* Remove deprecated methods and decorators:

  * ``(Async)YouTubeNotifier.listener()``
  * ``(Async)YouTubeNotifier.add_listener()``
  * ``AsyncYouTubeNotifier.serve()``

To migrate to version 3.0.0, see :doc:`migration`

**Full Changelog**: https://github.com/SeoulSKY/ytnoti/compare/v2.1.4...v3.0.0

v2.1.4
------

* Improve type hints for function parameters and return types. Previously, it didn't follow the best practices, such as using Any for keywords parameters.
* Update dependencies to the latest versions.

**Full Changelog**: https://github.com/SeoulSKY/ytnoti/compare/v2.1.3...v2.1.4

v2.1.3
------

* Fix a race condition that can cause duplicated notifications.

**Full Changelog**: https://github.com/SeoulSKY/ytnoti/compare/v2.1.2...v2.1.3

v2.1.2
------

* Fix not properly handling errors when resubscribing to channels every day.
* Fix race conditions in ``InMemoryVideoHistory`` and ``FileVideoHistory``

**Full Changelog**: https://github.com/SeoulSKY/ytnoti/compare/v2.1.1...v2.1.2

v2.1.1
------

* Fix raising an error when receiving the push notification for deleted video.
* From now on, ``ytnoti`` explicitly raises ``RuntimeError`` when failed to parse the request body from YouTube. In the past, it logged the error to the logger.

**Full Changelog**: https://github.com/SeoulSKY/ytnoti/compare/v2.1.0...v2.1.1


v2.1.0
------

* From now on, ``YouTubeNotifier`` extends ``AsyncYouTubeNotifier`` and ``AsyncYouTubeNotifier`` extends ``object``. ``BaseYouTubeNotifier`` was removed.
* Added ``(Async)YouTubeNotifier.run_in_background()``. It works like the ``run()`` method but immediately returns when the notifier starts running.
* Added ``(Async) YouTubeNotifier.unsubscribe()``. It unsubscribes the subscribed channel IDs
* From now on, ``(Async)YouTubeNotifier.subscribe()`` immediately raises ``ValueError`` when the given channel IDs are invalid. It didn't raise an error in the past until the notifier started running.
* Improved the speed of verifying channel IDs

Deprecations
~~~~~~~~~~~~

The following methods are deprecated and will be removed in version ``3.0.0``
* ``AsyncYouTubeNotifier.serve()`` -> ``use AsyncYouTubeNotifier.run()``
* ``(Async)YouTubeNotifier.add_listener()`` -> use either ``add_any_listener()``, ``add_upload_listener()``, or ``add_edit_listener()``

The following decorators are deprecated and will be removed in version ``3.0.0``
* ``(Async)YouTubeNotifier.listener()`` -> use either ``any``, ``upload`` or ``edit``

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