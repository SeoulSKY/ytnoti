"""
This module defines Enum classes used in the package.
"""

from enum import Enum


class NotificationKind(Enum):
    """
    Enum for the kind of notification
    """

    UPLOAD = 0
    """Upload notification"""

    EDIT = 1
    """Edit notification"""

    ANY = 2
    """Any notification"""


class ServerMode(Enum):
    """
    Enum for the server mode
    """

    RUN = "run"
    """Create an event loop and run the server"""

    SERVE = "serve"
    """Serve the server in the existing event loop"""
