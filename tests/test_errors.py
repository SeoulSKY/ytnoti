"""Test errors."""

from http import HTTPStatus

from ytnoti.errors import HTTPError


def test_http_errors() -> None:
    """Test creating HTTPError instances."""
    error = HTTPError("test", 400)
    assert isinstance(error.status_code, HTTPStatus)

    error = HTTPError("test", HTTPStatus.BAD_REQUEST)
    assert isinstance(error.status_code, HTTPStatus)

    assert error.message in str(error)
    assert "400" in str(error)
