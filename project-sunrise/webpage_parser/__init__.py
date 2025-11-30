"""
Webpage Parser - A modern, flexible Python library for parsing web pages.
"""

from .parser import WebpageParser
from .async_parser import AsyncWebpageParser
from .models import ParseResult, Element
from .exceptions import (
    ParserError,
    NetworkError,
    ParseError,
    TimeoutError,
)

__version__ = "0.1.0"
__all__ = [
    "WebpageParser",
    "AsyncWebpageParser",
    "ParseResult",
    "Element",
    "ParserError",
    "NetworkError",
    "ParseError",
    "TimeoutError",
]

