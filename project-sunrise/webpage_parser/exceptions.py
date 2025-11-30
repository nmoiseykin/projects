"""
Custom exceptions for webpage parser.
"""


class ParserError(Exception):
    """Base exception for all parser errors."""

    pass


class NetworkError(ParserError):
    """Raised when there's a network-related error."""

    pass


class ParseError(ParserError):
    """Raised when there's an error parsing content."""

    pass


class TimeoutError(ParserError):
    """Raised when a request times out."""

    pass

