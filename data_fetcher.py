"""
Data Fetcher Module (ROBUST VERSION)
Fetches stock data from Yahoo Finance with proper error handling and retries
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, time, timedelta
import pytz
from logs import logger, performance_tracker
import config
import time as time_module

class DataFetcher:
    def __init__(self):
        """Initialize data fetcher"""
        self.rate_limit_delay = config.API_RATE_LIMIT
        self.ist_tz = pytz.timezone('Asia/Kolkata')
        self.max_retries = 2
        self.cache = {}
        self.cache_duration = 60  # Cache for 60 seconds
        
        logger.info("Data Fetcher initialized")
    
    def fetch_stock_data(self, symbol, period='5d', interval='5m', retry_count=0):
        """
        Fetch stock data from Yahoo Finance with retries and caching
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS')
            period: Data period ('1d', '5d', '1mo', etc.)
            interval: Candle interval ('1m', '5m', '15m', '1h', '1d')
            retry_count: Current retry attempt
        
        Returns:
            DataFrame with OHLCV data or None
        """
        try:
            # Check cache first (reduce API calls)
            cache_key = f"{symbol}_{period}_{interval}"
            if cache_key in self.cache:
                cache_time, cached_df = self.cache[cache_key]
                if (datetime.now() - cache_time).total_seconds() < self.cache_duration:
                    logger.debug(f"Using cached data for {symbol}")
                    return cached_df.copy()
            
            performance_tracker.increment_api_calls()
            
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Fetch data with explicit parameters
            logger.debug(f"Fetching {symbol}: period={period}, interval={interval}")
            
            # METHOD 1: Try download first (more reliable)
            try:
                df = yf.download(
                    tickers=symbol,
                    period=period,
                    interval=interval,
                    progress=False,
                    show_errors=False,
                    threads=False  # Single-threaded for reliability
                )
            except Exception as e:
                logger.debug(f"download() failed for {symbol}: {str(e)}")
                # METHOD 2: Fallback to ticker.history
                df = ticker.history(
                    period=period,
                    interval=interval,
                    actions=False,
                    auto_adjust=True,
                    back_adjust=False,
                    repair=False,
                    keepna=False,
                    proxy=None,
                    rounding=False,
                    timeout=10
                )
            
            # Validate data
            if df is None or len(df) == 0:
                logger.debug(f"No data returned for {symbol}")
                
                # RETRY LOGIC
                if retry_count < self.max_retries:
                    logger.debug(f"Retrying {symbol} (attempt {retry_count + 1}/{self.max_retries})")
                    time_module.sleep(2)  # Wait before retry
                    return self.fetch_stock_data(symbol, period, interval, retry_count + 1)
                
                return None
            
            # Clean data
            df = df.dropna()
            
            if len(df) == 0:
                logger.debug(f"Empty dataframe after cleaning for {symbol}")
                return None
            
            # Ensure proper column names (yf.download uses different format)
            if 'Close' not in df.columns and 'close' in df.columns:
                df.rename(columns={
                    'open': 'Open',
                    'high': 'High',
                    'low': 'Low',
                    'close': 'Close',
                    'volume': 'Volume'
                }, inplace=True)
            
            # Store in cache
            self.cache[cache_key] = (datetime.now(), df.copy())
            
            # Rate limiting
            time_module.sleep(self.rate_limit_delay)
            
            logger.debug(f"✅ {symbol}: Fetched {len(df)} candles")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            performance_tracker.increment_errors()
            
            # RETRY on exception
            if retry_count < self.max_retries:
                logger.debug(f"Retrying {symbol} after exception (attempt {retry_count + 1}/{self.max_retries})")
                time_module.sleep(2)
                return self.fetch_stock_data(symbol, period, interval, retry_count + 1)
            
            return None
    
    def fetch_intraday_data(self, symbol):
        """
        Fetch intraday data - optimized for 5-minute charts
        Uses 1d period to reduce API load
        """
        try:
            # For intraday, 1 day of data is sufficient
            df = self.fetch_stock_data(symbol, period='1d', interval='5m')
            
            if df is not None and len(df) >= 10:
                return df
            
            # Fallback: Try 2 days if 1 day insufficient
            logger.debug(f"{symbol}: 1d insufficient, trying 2d")
            df = self.fetch_stock_data(symbol, period='2d', interval='5m')
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching intraday for {symbol}: {str(e)}")
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
                minutes_left = ((market_open.hour * 60 + market_open.minute) - 
                               (current_time.hour * 60 + current_time.minute))
                return False, f"Market opens in {minutes_left} min"
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
            df = self.fetch_stock_data(symbol, period='1d', interval='1m')
            
            if df is None or len(df) == 0:
                return None
            
            return df['Close'].iloc[-1]
            
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
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache = {}
        logger.info("Cache cleared")
    
    def test_connection(self):
        """
        Test if yfinance connection is working
        Returns: (success: bool, message: str)
        """
        try:
            logger.info("Testing yfinance connection...")
            df = self.fetch_stock_data("RELIANCE.NS", period="1d", interval="5m")
            
            if df is not None and len(df) > 0:
                logger.info(f"✅ Connection test passed: {len(df)} candles")
                return True, f"Success: {len(df)} candles fetched"
            else:
                logger.error("❌ Connection test failed: No data")
                return False, "No data received"
                
        except Exception as e:
            logger.error(f"❌ Connection test failed: {str(e)}")
            return False, str(e)
