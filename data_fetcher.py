"""
Data Fetcher Module
Fetches stock data from Yahoo Finance
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, time
import pytz
from logs import logger, performance_tracker
import config
import time as time_module

class DataFetcher:
    def __init__(self):
        """Initialize data fetcher"""
        self.rate_limit_delay = config.API_RATE_LIMIT
        self.ist_tz = pytz.timezone('Asia/Kolkata')
    
    def fetch_stock_data(self, symbol, period='5d', interval='5m'):
        """
        Fetch stock data from Yahoo Finance
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS')
            period: Data period ('1d', '5d', '1mo', etc.)
            interval: Candle interval ('1m', '5m', '15m', '1h', '1d')
        
        Returns:
            DataFrame with OHLCV data or None
        """
        try:
            performance_tracker.increment_api_calls()
            
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Fetch data
            df = ticker.history(period=period, interval=interval)
            
            if df is None or len(df) == 0:
                logger.debug(f"No data returned for {symbol}")
                return None
            
            # Clean data
            df = df.dropna()
            
            if len(df) == 0:
                return None
            
            # Rate limiting
            time_module.sleep(self.rate_limit_delay)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            performance_tracker.increment_errors()
            return None
    
    def get_market_status(self):
        """
        Check if Indian stock market is open
        
        Returns:
            (is_open: bool, status_message: str)
        """
        try:
            now = datetime.now(self.ist_tz)
            current_time = now.time()
            current_day = now.weekday()  # 0 = Monday, 6 = Sunday
            
            # Market closed on weekends
            if current_day >= 5:  # Saturday or Sunday
                return False, "Market closed (Weekend)"
            
            # Market hours: 9:15 AM to 3:30 PM IST
            market_open = time(
                config.MARKET_OPEN_HOUR, 
                config.MARKET_OPEN_MINUTE
            )
            market_close = time(
                config.MARKET_CLOSE_HOUR, 
                config.MARKET_CLOSE_MINUTE
            )
            
            if market_open <= current_time <= market_close:
                return True, "Market OPEN"
            elif current_time < market_open:
                return False, f"Market opens at {market_open.strftime('%I:%M %p')}"
            else:
                return False, "Market closed for the day"
                
        except Exception as e:
            logger.error(f"Error checking market status: {str(e)}")
            return False, "Unknown"
    
    def get_current_price(self, symbol):
        """
        Get current price of a stock
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Current price or None
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='1d', interval='1m')
            
            if data is None or len(data) == 0:
                return None
            
            return data['Close'].iloc[-1]
            
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {str(e)}")
            return None
    
    def validate_data(self, df, min_candles=20):
        """
        Validate if dataframe has sufficient data
        
        Args:
            df: DataFrame to validate
            min_candles: Minimum required candles
        
        Returns:
            bool: True if valid
        """
        if df is None:
            return False
        
        if len(df) < min_candles:
            return False
        
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required_columns):
            return False
        
        return True
