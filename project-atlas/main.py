#!/usr/bin/env python3
"""
Main CLI interface for project-atlas
Builds trading charts from PostgreSQL OHLC data
"""
import argparse
from datetime import datetime
from database import DatabaseConnection
from chart_builder import ChartBuilder
from config import TIMEFRAMES


def parse_date(date_string: str) -> datetime:
    """Parse date string in format YYYY-MM-DD or YYYY-MM-DD HH:MM"""
    try:
        # Try with time first
        return datetime.strptime(date_string, '%Y-%m-%d %H:%M')
    except ValueError:
        # Fall back to date only
        return datetime.strptime(date_string, '%Y-%m-%d')


def main():
    parser = argparse.ArgumentParser(
        description='Build trading charts from PostgreSQL OHLC data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  python main.py --timeframe 5m --start "2025-09-01" --end "2025-09-10"
  python main.py --timeframe 1h --start "2025-09-01 00:00" --end "2025-09-10 23:59" --output my_chart.html
  python main.py --timeframe 15m --start "2025-09-01" --end "2025-09-10" --no-volume

Supported timeframes: {', '.join(TIMEFRAMES)}
        """
    )
    
    parser.add_argument(
        '--timeframe', '-t',
        type=str,
        required=True,
        choices=TIMEFRAMES,
        help='Timeframe for the chart (1m, 5m, 15m, 30m, 1h, 4h)'
    )
    
    parser.add_argument(
        '--start', '-s',
        type=str,
        required=True,
        help='Start date (YYYY-MM-DD or YYYY-MM-DD HH:MM)'
    )
    
    parser.add_argument(
        '--end', '-e',
        type=str,
        required=True,
        help='End date (YYYY-MM-DD or YYYY-MM-DD HH:MM)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='Output HTML filename (default: auto-generated)'
    )
    
    parser.add_argument(
        '--no-volume',
        action='store_true',
        help='Hide volume subplot'
    )
    
    parser.add_argument(
        '--show',
        action='store_true',
        help='Display chart in browser instead of saving'
    )
    
    parser.add_argument(
        '--title',
        type=str,
        default=None,
        help='Custom chart title'
    )
    
    args = parser.parse_args()
    
    # Parse dates
    try:
        start_date = parse_date(args.start)
        end_date = parse_date(args.end)
    except ValueError as e:
        print(f"Error parsing dates: {e}")
        print("Expected format: YYYY-MM-DD or YYYY-MM-DD HH:MM")
        return 1
    
    if start_date >= end_date:
        print("Error: Start date must be before end date")
        return 1
    
    # Connect to database and fetch data
    try:
        with DatabaseConnection() as db:
            print(f"Fetching {args.timeframe} data from {start_date} to {end_date}...")
            df = db.get_candles(args.timeframe, start_date, end_date)
            
            if df.empty:
                print("No data found. Please check:")
                print(f"  - Table 'candles_{args.timeframe}' exists")
                print(f"  - Data exists for the specified date range")
                print(f"  - Database connection settings in config.py")
                return 1
            
            # Build chart
            chart_builder = ChartBuilder(df, args.timeframe, start_date, end_date)
            
            if args.show:
                print("Displaying chart in browser...")
                chart_builder.show_chart(show_volume=not args.no_volume)
            else:
                filename = chart_builder.save_chart(
                    filename=args.output,
                    show_volume=not args.no_volume
                )
                print(f"\n✓ Chart generated successfully!")
                print(f"  Open {filename} in your browser to view the chart.")
            
            return 0
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())

