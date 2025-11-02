"""
Technical Indicators Analyzer
Calculates RSI, Support/Resistance, Volume Analysis
"""

import pandas as pd
import numpy as np
from logs import logger
import config

class IndicatorAnalyzer:
    def __init__(self):
        """Initialize indicator analyzer"""
        self.rsi_period = config.RSI_PERIOD
        self.volume_period = config.VOLUME_MA_PERIOD
    
    def calculate_rsi(self, df, period=None):
        """
        Calculate RSI (Relative Strength Index)
        
        Args:
            df: DataFrame with 'Close' column
            period: RSI period (default from config)
        
        Returns:
            Series with RSI values
        """
        if period is None:
            period = self.rsi_period
        
        try:
            close = df['Close']
            delta = close.diff()
            
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {str(e)}")
            return pd.Series([50] * len(df))
    
    def calculate_support_resistance(self, df, lookback=None):
        """
        Calculate support and resistance levels using pivot points
        
        Args:
            df: DataFrame with OHLC data
            lookback: Number of candles to look back
        
        Returns:
            (support_levels, resistance_levels): Lists of price levels
        """
        if lookback is None:
            lookback = config.SR_LOOKBACK_DAYS
        
        try:
            # Use recent data for S/R calculation
            recent_df = df.tail(lookback) if len(df) > lookback else df
            
            # Find local highs and lows
            highs = recent_df['High'].values
            lows = recent_df['Low'].values
            closes = recent_df['Close'].values
            
            # Calculate pivot points
            resistance_levels = []
            support_levels = []
            
            # Method 1: Local extrema
            for i in range(2, len(recent_df) - 2):
                # Resistance: Local high
                if (highs[i] > highs[i-1] and highs[i] > highs[i-2] and
                    highs[i] > highs[i+1] and highs[i] > highs[i+2]):
                    resistance_levels.append(highs[i])
                
                # Support: Local low
                if (lows[i] < lows[i-1] and lows[i] < lows[i-2] and
                    lows[i] < lows[i+1] and lows[i] < lows[i+2]):
                    support_levels.append(lows[i])
            
            # Method 2: Recent swing highs/lows
            recent_high = recent_df['High'].max()
            recent_low = recent_df['Low'].min()
            resistance_levels.append(recent_high)
            support_levels.append(recent_low)
            
            # Method 3: Round numbers (psychological levels)
            current_price = closes[-1]
            price_range = recent_high - recent_low
            
            if price_range > 0:
                # Find round numbers near current price
                step = 10 ** (len(str(int(current_price))) - 2)  # Round to appropriate decimal
                
                for multiplier in range(-3, 4):
                    level = round(current_price / step) * step + (multiplier * step)
                    if recent_low <= level <= recent_high:
                        if level > current_price:
                            resistance_levels.append(level)
                        elif level < current_price:
                            support_levels.append(level)
            
            # Remove duplicates and sort
            support_levels = sorted(list(set([round(x, 2) for x in support_levels])))
            resistance_levels = sorted(list(set([round(x, 2) for x in resistance_levels])))
            
            # Filter: Keep only levels near current price
            current_price = closes[-1]
            
            # Support levels below current price
            support_levels = [s for s in support_levels if s < current_price]
            support_levels = sorted(support_levels, reverse=True)[:5]  # Top 5 closest
            
            # Resistance levels above current price
            resistance_levels = [r for r in resistance_levels if r > current_price]
            resistance_levels = sorted(resistance_levels)[:5]  # Top 5 closest
            
            return support_levels, resistance_levels
            
        except Exception as e:
            logger.error(f"Error calculating S/R: {str(e)}")
            return [], []
    
    def check_volume_confirmation(self, df, period=None):
        """
        Check if current volume is above average
        
        Args:
            df: DataFrame with 'Volume' column
            period: MA period for volume
        
        Returns:
            (is_confirmed: bool, volume_ratio: float)
        """
        if period is None:
            period = self.volume_period
        
        try:
            if len(df) < period:
                return False, 1.0
            
            current_volume = df['Volume'].iloc[-1]
            avg_volume = df['Volume'].tail(period).mean()
            
            if avg_volume == 0:
                return False, 1.0
            
            volume_ratio = current_volume / avg_volume
            is_confirmed = volume_ratio >= config.MIN_VOLUME_RATIO
            
            return is_confirmed, volume_ratio
            
        except Exception as e:
            logger.error(f"Error checking volume: {str(e)}")
            return False, 1.0
    
    def calculate_atr(self, df, period=14):
        """
        Calculate Average True Range (ATR)
        
        Args:
            df: DataFrame with OHLC data
            period: ATR period
        
        Returns:
            Series with ATR values
        """
        try:
            high = df['High']
            low = df['Low']
            close = df['Close']
            
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=period).mean()
            
            return atr
            
        except Exception as e:
            logger.error(f"Error calculating ATR: {str(e)}")
            return pd.Series([0] * len(df))
    
    def is_near_level(self, price, level, threshold_percent=None):
        """
        Check if price is near a key level
        
        Args:
            price: Current price
            level: Key level to check
            threshold_percent: Distance threshold in percentage
        
        Returns:
            bool: True if near level
        """
        if threshold_percent is None:
            threshold_percent = config.SR_TOUCH_THRESHOLD
        
        distance = abs(price - level) / level * 100
        return distance <= threshold_percent
