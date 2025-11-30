#!/bin/bash
# Script to fetch ForexFactory calendar using curl with browser-like headers

URL="${1:-https://www.forexfactory.com/calendar}"
OUTPUT="${2:-forexfactory_calendar.html}"

echo "Fetching ForexFactory calendar..."
echo "URL: $URL"
echo "Output: $OUTPUT"

curl -L "$URL" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8" \
  -H "Accept-Language: en-US,en;q=0.5" \
  -H "Accept-Encoding: gzip, deflate, br" \
  -H "DNT: 1" \
  -H "Connection: keep-alive" \
  -H "Upgrade-Insecure-Requests: 1" \
  -H "Sec-Fetch-Dest: document" \
  -H "Sec-Fetch-Mode: navigate" \
  -H "Sec-Fetch-Site: none" \
  -H "Cache-Control: max-age=0" \
  --compressed \
  -o "$OUTPUT"

if [ $? -eq 0 ]; then
  echo "Successfully saved to $OUTPUT"
  echo "Now parse it with: python3 parse_forex_calendar_advanced.py --html-file $OUTPUT"
else
  echo "Failed to fetch calendar"
  exit 1
fi

