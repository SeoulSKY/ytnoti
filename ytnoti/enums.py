"""
This module defines Enum classes used in the package.

Classes:
    NotificationKind
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
