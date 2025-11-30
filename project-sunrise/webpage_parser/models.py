"""
Data models for webpage parser.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from bs4 import BeautifulSoup, Tag


@dataclass
class Element:
    """
    Represents an HTML element.
    """

    tag: str
    text: str
    attrs: Dict[str, Any]
    html: str

    @classmethod
    def from_tag(cls, tag: Tag) -> "Element":
        """Create Element from BeautifulSoup Tag."""
        return cls(
            tag=tag.name,
            text=tag.get_text(strip=True),
            attrs=dict(tag.attrs),
            html=str(tag),
        )


@dataclass
class ParseResult:
    """
    Contains the parsed webpage data.
    """

    url: str
    title: str
    text: str
    links: List[Dict[str, str]]
    images: List[Dict[str, str]]
    metadata: Dict[str, str]
    structured_data: List[Dict[str, Any]]
    soup: Optional[BeautifulSoup] = None

    def select(self, selector: str) -> Optional[Element]:
        """
        Select a single element using CSS selector.

        Args:
            selector: CSS selector string

        Returns:
            Element object or None if not found
        """
        if not self.soup:
            return None

        tag = self.soup.select_one(selector)
        if tag:
            return Element.from_tag(tag)
        return None

    def select_all(self, selector: str, text: bool = False) -> List[Element]:
        """
        Select multiple elements using CSS selector.

        Args:
            selector: CSS selector string
            text: If True, return list of text strings instead of Element objects

        Returns:
            List of Element objects or text strings
        """
        if not self.soup:
            return []

        tags = self.soup.select(selector)

        if text:
            return [tag.get_text(strip=True) for tag in tags]

        return [Element.from_tag(tag) for tag in tags]

    def get_links_by_text(self, text: str, exact: bool = False) -> List[Dict[str, str]]:
        """
        Get links that contain specific text.

        Args:
            text: Text to search for
            exact: If True, match exact text; otherwise, partial match

        Returns:
            List of link dictionaries
        """
        if exact:
            return [link for link in self.links if link["text"] == text]
        else:
            text_lower = text.lower()
            return [link for link in self.links if text_lower in link["text"].lower()]

    def get_images_by_alt(self, alt: str, exact: bool = False) -> List[Dict[str, str]]:
        """
        Get images that contain specific alt text.

        Args:
            alt: Alt text to search for
            exact: If True, match exact text; otherwise, partial match

        Returns:
            List of image dictionaries
        """
        if exact:
            return [img for img in self.images if img["alt"] == alt]
        else:
            alt_lower = alt.lower()
            return [img for img in self.images if alt_lower in img["alt"].lower()]

    def __repr__(self) -> str:
        return (
            f"ParseResult(url='{self.url}', title='{self.title[:50]}...', "
            f"links={len(self.links)}, images={len(self.images)})"
        )

