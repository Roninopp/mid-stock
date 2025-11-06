"""
Data Fetcher Module (OPTIMIZED FOR 5-MINUTE SCANNING)
Per-scan caching - each stock fetched only ONCE per scan
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
        self.max_retries = 1  # Only 1 retry to avoid spam
        
        # Per-scan cache: Cleared every scan
        self.cache = {}
        self.scan_number = 0
        
        logger.info("Data Fetcher initialized (5-minute mode)")
    
    def start_new_scan(self):
        """Clear cache at start of new scan"""
        self.cache = {}
        self.scan_number += 1
        logger.debug(f"Scan #{self.scan_number} - Cache cleared")
    
    def fetch_stock_data(self, symbol, period='1d', interval='5m', retry_count=0):
        """
        Fetch stock data - only once per scan per symbol
        """
        try:
            cache_key = f"{symbol}_{period}_{interval}"
            
            # Check if already fetched THIS scan
            if cache_key in self.cache:
                logger.debug(f"Cache: {symbol}")
                return self.cache[cache_key].copy()
            
            # Track API call
            performance_tracker.increment_api_calls()
            logger.debug(f"API: {symbol}")
            
            # Fetch data using download (more reliable)
            df = yf.download(
                tickers=symbol,
                period=period,
                interval=interval,
                progress=False,
                show_errors=False,
                threads=False,
                timeout=15
            )
            
            # Validate
            if df is None or len(df) == 0:
                # ONE retry only
                if retry_count == 0:
                    logger.debug(f"Retry: {symbol}")
                    time_module.sleep(3)
                    return self.fetch_stock_data(symbol, period, interval, 1)
                
                logger.debug(f"Failed: {symbol}")
                return None
            
            # Clean
            df = df.dropna()
            if len(df) == 0:
                return None
            
            # Fix columns if needed
            if 'Close' not in df.columns:
                if 'close' in df.columns:
                    df.rename(columns={
                        'open': 'Open', 'high': 'High',
                        'low': 'Low', 'close': 'Close',
                        'volume': 'Volume'
                    }, inplace=True)
                else:
                    logger.error(f"Invalid columns for {symbol}: {df.columns.tolist()}")
                    return None
            
            # Cache for THIS scan
            self.cache[cache_key] = df.copy()
            
            # Rate limit (important!)
            time_module.sleep(self.rate_limit_delay)
            
            logger.debug(f"OK: {symbol} ({len(df)} candles)")
            return df
            
        except Exception as e:
            logger.error(f"Error {symbol}: {str(e)}")
            performance_tracker.increment_errors()
            
            # ONE retry
            if retry_count == 0:
                time_module.sleep(3)
                return self.fetch_stock_data(symbol, period, interval, 1)
            
            return None
    
    def fetch_intraday_data(self, symbol):
        """Fetch intraday 5-minute data"""
        try:
            # Use 1 day for 5-minute candles
            df = self.fetch_stock_data(symbol, period='1d', interval='5m')
            
            if df is not None and len(df) >= 10:
                return df
            
            # Fallback: Try 2 days
            logger.debug(f"Fallback 2d: {symbol}")
            df = self.fetch_stock_data(symbol, period='2d', interval='5m')
            
            return df
            
        except Exception as e:
            logger.error(f"Intraday error {symbol}: {str(e)}")
            return None
    
    def get_market_status(self):
        """Check if market is open"""
        try:
            now = datetime.now(self.ist_tz)
            current_time = now.time()
            current_day = now.weekday()
            
            if current_day >= 5:
                return False, "Weekend"
            
            market_open = time(config.MARKET_OPEN_HOUR, config.MARKET_OPEN_MINUTE)
            market_close = time(config.MARKET_CLOSE_HOUR, config.MARKET_CLOSE_MINUTE)
            
            if market_open <= current_time <= market_close:
                return True, "Market OPEN"
            elif current_time < market_open:
                mins = ((market_open.hour * 60 + market_open.minute) - 
                       (current_time.hour * 60 + current_time.minute))
                return False, f"Opens in {mins}min"
            else:
                return False, "Market closed"
                
        except Exception as e:
            logger.error(f"Market status error: {str(e)}")
            return False, "Unknown"
    
    def get_current_price(self, symbol):
        """Get current price"""
        try:
            df = self.fetch_stock_data(symbol, period='1d', interval='1m')
            return df['Close'].iloc[-1] if df is not None and len(df) > 0 else None
        except:
            return None
    
    def validate_data(self, df, min_candles=20):
        """Validate dataframe"""
        if df is None or len(df) < min_candles:
            return False
        cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        return all(c in df.columns for c in cols)
    
    def get_cache_stats(self):
        """Get cache stats"""
        return {
            'cached_stocks': len(self.cache),
            'scan_number': self.scan_number
        }
    
    def test_connection(self):
        """Test yfinance"""
        try:
            logger.info("Testing yfinance...")
            df = self.fetch_stock_data("RELIANCE.NS", period="1d", interval="5m")
            
            if df is not None and len(df) > 0:
                logger.info(f"✅ Test OK: {len(df)} candles")
                return True, f"{len(df)} candles"
            else:
                logger.error("❌ Test failed: No data")
                return False, "No data"
        except Exception as e:
            logger.error(f"❌ Test error: {str(e)}")
            return False, str(e)
