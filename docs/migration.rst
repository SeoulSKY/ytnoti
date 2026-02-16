Migration Guide
---------------

When you upgrade a major version of ``ytnoti``, you may need to update your code. Follow the migration guide below to update your code.

From v2.x.x to v3.x.x
=====================

The following methods are removed:
  * ``@notifier.listener()``
  * ``(Async)YouTubeNotifier.add_listener()``
  * ``AsyncYouTubeNotifier.serve()``

The following enums are removed:
  * ``NotificationKind`` - If your code uses this enum, please define on your own.

``@notifier.listener()``
~~~~~~~~~~~~~~~~~~~~~~~~

Use more specific decorators, ``@notifier.any()``, ``@notifier.delete()``, ``@notifier.upload()``, or ``@notifier.edit()`` instead.

``(Async)YouTubeNotifier.add_listener()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use more specific methods, ``(Async)YouTubeNotifier.add_any_listener()``, ``(Async)YouTubeNotifier.add_delete_listener()``, ``(Async)YouTubeNotifier.add_upload_listener()``, or ``(Async)YouTubeNotifier.add_edit_listener()`` instead.

``AsyncYouTubeNotifier.serve()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``AsyncYouTubeNotifier.run()`` instead.
