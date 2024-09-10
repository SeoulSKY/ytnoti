"""Defines Enum classes used in the package."""

__all__ = ["NotificationKind"]

from enum import Enum


class NotificationKind(Enum):
    """Enum for the kind of notification."""

    UPLOAD = 0
    """Upload notification"""

    EDIT = 1
    """Edit notification"""

    ANY = 2
    """Any notification"""
