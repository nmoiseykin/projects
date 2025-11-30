# Webpage Parser

A modern, flexible Python library for parsing and extracting data from web pages.

## Features

- 🚀 Simple and intuitive API
- 🔍 Extract text, links, images, and metadata
- 📊 Support for structured data extraction
- 🛡️ Built-in error handling and retry logic
- ⚡ Async support for efficient batch processing
- 🎯 CSS and XPath selector support

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Parse ForexFactory USD Calendar (Today's Events)

```bash
# Simple one-command run
./run_parser.sh

# Or run directly
cd examples
source ../venv/bin/activate
python3 parse_forexfactory_final.py
```

This will:
- ✅ Fetch today's economic calendar from ForexFactory.com
- ✅ Filter for USD currency only
- ✅ Save results to `examples/forex_calendar_usd.json`
- ✅ Display all USD events with impact levels, forecasts, and actual values

### Python API Usage

```python
from webpage_parser import WebpageParser

# Basic usage
parser = WebpageParser()
result = parser.parse("https://example.com")

print(f"Title: {result.title}")
print(f"Text: {result.text[:100]}...")
print(f"Links: {len(result.links)}")
print(f"Images: {len(result.images)}")
```

## Advanced Usage

### Custom Selectors

```python
from webpage_parser import WebpageParser, Selector

parser = WebpageParser()
result = parser.parse("https://example.com")

# Extract specific elements
articles = result.select("article.post")
titles = result.select_all("h2.title", text=True)
```

### Async Parsing

```python
import asyncio
from webpage_parser import AsyncWebpageParser

async def main():
    parser = AsyncWebpageParser()
    urls = ["https://example1.com", "https://example2.com"]
    
    results = await parser.parse_batch(urls)
    for result in results:
        print(f"{result.url}: {result.title}")

asyncio.run(main())
```

### Structured Data Extraction

```python
from webpage_parser import WebpageParser

parser = WebpageParser()
result = parser.parse("https://example.com")

# Extract metadata
metadata = result.metadata
print(f"Description: {metadata.get('description')}")
print(f"Keywords: {metadata.get('keywords')}")

# Extract JSON-LD structured data
structured_data = result.structured_data
print(structured_data)
```

## Configuration

```python
from webpage_parser import WebpageParser

parser = WebpageParser(
    timeout=30,
    max_retries=3,
    user_agent="Custom User Agent",
    follow_redirects=True
)
```

## API Reference

### WebpageParser

Main class for parsing web pages.

**Methods:**
- `parse(url: str) -> ParseResult`: Parse a single URL
- `parse_html(html: str, base_url: str = None) -> ParseResult`: Parse HTML string

### ParseResult

Contains parsed webpage data.

**Properties:**
- `url`: The webpage URL
- `title`: Page title
- `text`: Extracted text content
- `links`: List of links found
- `images`: List of image URLs
- `metadata`: Dictionary of meta tags
- `structured_data`: Extracted structured data (JSON-LD, microdata)

**Methods:**
- `select(selector: str) -> Element`: Select single element
- `select_all(selector: str) -> List[Element]`: Select multiple elements

## Examples

See the `examples/` directory for more usage examples.

## Testing

```bash
pytest tests/
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

