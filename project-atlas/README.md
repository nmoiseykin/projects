# Project Atlas - Trading Chart Builder

A Python application for building interactive trading charts from PostgreSQL OHLC (Open, High, Low, Close) and volume data.

## Features

- Support for multiple timeframes: 1m, 5m, 15m, 30m, 1h, 4h
- Interactive candlestick charts with volume
- Date range filtering
- Export charts to HTML
- Beautiful dark-themed visualizations using Plotly

## Requirements

- Python 3.7+
- PostgreSQL database with OHLC data tables
- Required Python packages (see `requirements.txt`)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure database connection in `config.py` or set environment variables:
   - `DB_HOST` (default: localhost)
   - `DB_PORT` (default: 5432)
   - `DB_NAME` (default: trading_db)
   - `DB_USER` (default: postgres)
   - `DB_PASSWORD` (default: postgres)

## Database Schema

The application expects tables named `candles_{timeframe}` (e.g., `candles_1m`, `candles_5m`, etc.) with the following structure:

```sql
CREATE TABLE candles_1m (
    timestamp TIMESTAMP PRIMARY KEY,
    open DECIMAL(10, 2),
    high DECIMAL(10, 2),
    low DECIMAL(10, 2),
    close DECIMAL(10, 2),
    volume DECIMAL(15, 2)
);

-- Repeat for other timeframes: candles_5m, candles_15m, candles_30m, candles_1h, candles_4h
```

## Usage

### Basic Example

Build a chart from September 1, 2025 to September 10, 2025 using 5-minute data:

```bash
python main.py --timeframe 5m --start "2025-09-01" --end "2025-09-10"
```

### Advanced Examples

```bash
# Specify custom output filename
python main.py --timeframe 1h --start "2025-09-01" --end "2025-09-10" --output my_chart.html

# Hide volume subplot
python main.py --timeframe 15m --start "2025-09-01" --end "2025-09-10" --no-volume

# Display chart in browser instead of saving
python main.py --timeframe 30m --start "2025-09-01" --end "2025-09-10" --show

# Use custom title
python main.py --timeframe 4h --start "2025-09-01" --end "2025-09-10" --title "My Trading Analysis"
```

### Command Line Options

- `--timeframe`, `-t`: Timeframe (required) - one of: 1m, 5m, 15m, 30m, 1h, 4h
- `--start`, `-s`: Start date (required) - format: YYYY-MM-DD or YYYY-MM-DD HH:MM
- `--end`, `-e`: End date (required) - format: YYYY-MM-DD or YYYY-MM-DD HH:MM
- `--output`, `-o`: Output HTML filename (optional)
- `--no-volume`: Hide volume subplot
- `--show`: Display chart in browser instead of saving
- `--title`: Custom chart title

## Project Structure

```
project-atlas/
├── main.py           # CLI interface
├── database.py       # PostgreSQL connection and queries
├── chart_builder.py  # Chart visualization logic
├── config.py         # Configuration settings
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

## Example Output

The application generates interactive HTML charts with:
- Candlestick price chart
- Volume bars (color-coded: green for up, red for down)
- Zoom and pan capabilities
- Hover tooltips with OHLC data

## Troubleshooting

1. **Connection Error**: Check your PostgreSQL connection settings in `config.py`
2. **No Data Found**: Verify that:
   - The table `candles_{timeframe}` exists
   - Data exists for the specified date range
   - Column names match: timestamp, open, high, low, close, volume
3. **Import Errors**: Make sure all dependencies are installed: `pip install -r requirements.txt`

## License

This project is provided as-is for trading chart visualization purposes.

