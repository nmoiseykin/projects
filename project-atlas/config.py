"""
Configuration file for database connection
"""
import os

# PostgreSQL connection settings
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'aurora_db'),
    'user': os.getenv('DB_USER', 'aurora_user'),
    'password': os.getenv('DB_PASSWORD', 'aurora_pass123')
}

# Supported timeframes
TIMEFRAMES = ['1m', '5m', '15m', '30m', '1h', '4h']

# Table name pattern (assuming tables are named like: candles_1m, candles_5m, etc.)
TABLE_PATTERN = 'candles_{timeframe}'

