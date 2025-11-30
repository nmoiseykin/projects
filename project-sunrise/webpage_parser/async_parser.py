"""
Async webpage parser module for efficient batch processing.
"""

import asyncio
import aiohttp
from typing import List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from .models import ParseResult
from .exceptions import NetworkError, ParseError, TimeoutError as ParserTimeoutError


class AsyncWebpageParser:
    """
    Async webpage parser for efficient batch processing.
    """

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        user_agent: Optional[str] = None,
        follow_redirects: bool = True,
        verify_ssl: bool = True,
        max_concurrent: int = 10,
    ):
        """
        Initialize the AsyncWebpageParser.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            user_agent: Custom user agent string
            follow_redirects: Whether to follow HTTP redirects
            verify_ssl: Whether to verify SSL certificates
            max_concurrent: Maximum number of concurrent requests
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.follow_redirects = follow_redirects
        self.verify_ssl = verify_ssl
        self.max_concurrent = max_concurrent

        self.headers = {
            "User-Agent": user_agent
            or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    async def parse(self, url: str) -> ParseResult:
        """
        Parse a webpage from a URL asynchronously.

        Args:
            url: The URL to parse

        Returns:
            ParseResult object containing parsed data

        Raises:
            NetworkError: If there's a network-related error
            ParseError: If there's an error parsing the content
            TimeoutError: If the request times out
        """
        html = await self._fetch(url)
        return self.parse_html(html, base_url=url)

    async def parse_batch(self, urls: List[str]) -> List[ParseResult]:
        """
        Parse multiple URLs concurrently.

        Args:
            urls: List of URLs to parse

        Returns:
            List of ParseResult objects
        """
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def parse_with_semaphore(url: str):
            async with semaphore:
                try:
                    return await self.parse(url)
                except Exception as e:
                    # Return error result instead of raising
                    return ParseResult(
                        url=url,
                        title="",
                        text=f"Error: {str(e)}",
                        links=[],
                        images=[],
                        metadata={},
                        structured_data=[],
                        soup=None,
                    )

        tasks = [parse_with_semaphore(url) for url in urls]
        return await asyncio.gather(*tasks)

    def parse_html(self, html: str, base_url: Optional[str] = None) -> ParseResult:
        """
        Parse HTML content directly.

        Args:
            html: HTML string to parse
            base_url: Base URL for resolving relative links

        Returns:
            ParseResult object containing parsed data

        Raises:
            ParseError: If there's an error parsing the content
        """
        try:
            soup = BeautifulSoup(html, "lxml")
            return self._extract_data(soup, base_url)
        except Exception as e:
            raise ParseError(f"Error parsing HTML: {str(e)}")

    async def _fetch(self, url: str) -> str:
        """
        Fetch HTML content from a URL with retry logic.

        Args:
            url: The URL to fetch

        Returns:
            HTML content as string

        Raises:
            NetworkError: If there's a network-related error
            TimeoutError: If the request times out
        """
        connector = aiohttp.TCPConnector(ssl=self.verify_ssl)
        timeout = aiohttp.ClientTimeout(total=self.timeout)

        last_exception = None

        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession(
                    connector=connector, timeout=timeout, headers=self.headers
                ) as session:
                    async with session.get(url, allow_redirects=self.follow_redirects) as response:
                        response.raise_for_status()
                        return await response.text()

            except asyncio.TimeoutError as e:
                last_exception = e
                if attempt == self.max_retries - 1:
                    raise ParserTimeoutError(f"Request timed out after {self.max_retries} attempts: {url}")

            except aiohttp.ClientError as e:
                last_exception = e
                if attempt == self.max_retries - 1:
                    raise NetworkError(f"Network error after {self.max_retries} attempts: {str(e)}")

        raise NetworkError(f"Failed to fetch URL: {str(last_exception)}")

    def _extract_data(self, soup: BeautifulSoup, base_url: Optional[str]) -> ParseResult:
        """
        Extract data from BeautifulSoup object.

        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links

        Returns:
            ParseResult object
        """
        # Extract title
        title = ""
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)

        # Extract text content
        for script in soup(["script", "style", "noscript"]):
            script.decompose()

        text = soup.get_text(separator=" ", strip=True)

        # Extract links
        links = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if base_url:
                href = urljoin(base_url, href)
            link_text = link.get_text(strip=True)
            links.append({"url": href, "text": link_text})

        # Extract images
        images = []
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if src and base_url:
                src = urljoin(base_url, src)
            alt = img.get("alt", "")
            if src:
                images.append({"url": src, "alt": alt})

        # Extract metadata
        metadata = {}
        for meta in soup.find_all("meta"):
            name = meta.get("name", meta.get("property", ""))
            content = meta.get("content", "")
            if name and content:
                metadata[name] = content

        # Extract structured data (JSON-LD)
        structured_data = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                import json
                data = json.loads(script.string)
                structured_data.append(data)
            except:
                pass

        return ParseResult(
            url=base_url or "",
            title=title,
            text=text,
            links=links,
            images=images,
            metadata=metadata,
            structured_data=structured_data,
            soup=soup,
        )

