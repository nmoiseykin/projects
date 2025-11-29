"""
Chart visualization module using Plotly
"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime


class ChartBuilder:
    """Builds trading charts from OHLC data"""
    
    def __init__(self, df: pd.DataFrame, timeframe: str, start_date: datetime, end_date: datetime):
        """
        Initialize chart builder
        
        Args:
            df: DataFrame with OHLC data (columns: timestamp, open, high, low, close, volume)
            timeframe: Timeframe string (e.g., '5m', '1h')
            start_date: Start date for the chart
            end_date: End date for the chart
        """
        self.df = df.copy()
        self.timeframe = timeframe
        self.start_date = start_date
        self.end_date = end_date
        
        # Ensure timestamp is datetime
        if 'timestamp' in self.df.columns:
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
    
    def build_chart(self, show_volume: bool = True, title: str = None) -> go.Figure:
        """
        Build a candlestick chart with volume
        
        Args:
            show_volume: Whether to show volume subplot
            title: Custom chart title (auto-generated if None)
        
        Returns:
            Plotly Figure object
        """
        if self.df.empty:
            raise ValueError("Cannot build chart: DataFrame is empty")
        
        # Create subplots
        if show_volume:
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                row_heights=[0.7, 0.3],
                subplot_titles=('Price', 'Volume')
            )
        else:
            fig = make_subplots(
                rows=1, cols=1,
                subplot_titles=('Price',)
            )
        
        # Add candlestick chart
        candlestick = go.Candlestick(
            x=self.df['timestamp'],
            open=self.df['open'],
            high=self.df['high'],
            low=self.df['low'],
            close=self.df['close'],
            name='Price'
        )
        
        fig.add_trace(candlestick, row=1, col=1)
        
        # Add volume bars if requested
        if show_volume and 'volume' in self.df.columns:
            colors = ['red' if self.df['close'].iloc[i] < self.df['open'].iloc[i] 
                     else 'green' for i in range(len(self.df))]
            
            volume_bars = go.Bar(
                x=self.df['timestamp'],
                y=self.df['volume'],
                name='Volume',
                marker_color=colors
            )
            fig.add_trace(volume_bars, row=2, col=1)
        
        # Set title
        if title is None:
            title = f"Trading Chart - {self.timeframe} | {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}"
        
        fig.update_layout(
            title=title,
            xaxis_title='Time',
            yaxis_title='Price',
            template='plotly_dark',
            height=800,
            showlegend=True,
            xaxis_rangeslider_visible=False
        )
        
        # Update y-axis labels
        if show_volume:
            fig.update_yaxes(title_text="Price", row=1, col=1)
            fig.update_yaxes(title_text="Volume", row=2, col=1)
        
        # Format x-axis
        fig.update_xaxes(
            type='date',
            tickformat='%Y-%m-%d %H:%M'
        )
        
        return fig
    
    def save_chart(self, filename: str = None, show_volume: bool = True):
        """
        Build and save chart to HTML file
        
        Args:
            filename: Output filename (auto-generated if None)
            show_volume: Whether to show volume subplot
        """
        if filename is None:
            filename = f"chart_{self.timeframe}_{self.start_date.strftime('%Y%m%d')}_{self.end_date.strftime('%Y%m%d')}.html"
        
        fig = self.build_chart(show_volume=show_volume)
        fig.write_html(filename)
        print(f"Chart saved to {filename}")
        return filename
    
    def show_chart(self, show_volume: bool = True):
        """
        Build and display chart in browser
        
        Args:
            show_volume: Whether to show volume subplot
        """
        fig = self.build_chart(show_volume=show_volume)
        fig.show()

