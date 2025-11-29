"""
Database connection and query module
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from config import DB_CONFIG
import pandas as pd
from datetime import datetime


class DatabaseConnection:
    """Handles PostgreSQL database connections and queries"""
    
    def __init__(self):
        self.conn = None
        self.connect()
    
    def connect(self):
        """Establish connection to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                database=DB_CONFIG['database'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password']
            )
            print(f"Connected to PostgreSQL at {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        except psycopg2.Error as e:
            print(f"Error connecting to database: {e}")
            raise
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("Database connection closed")
    
    def get_candles(self, timeframe: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Fetch OHLC candles for a given timeframe and date range
        
        Args:
            timeframe: One of '1m', '5m', '15m', '30m', '1h', '4h'
            start_date: Start datetime
            end_date: End datetime
        
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        if timeframe not in ['1m', '5m', '15m', '30m', '1h', '4h']:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        
        # Construct table name (assuming format: candles_1m, candles_5m, etc.)
        table_name = f"candles_{timeframe}"
        
        # Query to fetch OHLC data
        query = f"""
        SELECT 
            timestamp,
            open,
            high,
            low,
            close,
            volume
        FROM {table_name}
        WHERE timestamp >= %s AND timestamp <= %s
        ORDER BY timestamp ASC
        """
        
        try:
            df = pd.read_sql_query(
                query,
                self.conn,
                params=(start_date, end_date)
            )
            
            if df.empty:
                print(f"Warning: No data found for {timeframe} between {start_date} and {end_date}")
            else:
                print(f"Fetched {len(df)} candles for {timeframe}")
            
            return df
            
        except psycopg2.Error as e:
            print(f"Error querying database: {e}")
            raise
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

