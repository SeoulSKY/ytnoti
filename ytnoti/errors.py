"""
This module contains custom exceptions for the ytnoti package.
"""

from http import HTTPStatus


class HTTPError(Exception):
    """
    Exception raised when an HTTP error occurs.
    """

    def __init__(self, message: str, status_code: int | HTTPStatus):
        """
        Initialize the HTTPError object.

        :param message: The error message
        :param status_code: The status code of the error
        """
        self.status_code = status_code if isinstance(status_code, HTTPStatus) else HTTPStatus(status_code)
        self.message = message

    def __str__(self):
        return f"Status code: {self.status_code}: {self.message}"
