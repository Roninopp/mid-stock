"""
False Breakout Detector Module
Detects fakeouts when price breaks a level then reverses back
"""

import pandas as pd
import numpy as np
from logs import logger, log_exceptions
import config

class FalseBreakoutDetector:
    def __init__(self):
        """Initialize false breakout detector"""
        self.confirmation_candles = config.BREAKOUT_CONFIRMATION_CANDLES
        self.volume_multiplier = config.BREAKOUT_VOLUME_MULTIPLIER
        
    @log_exceptions
    def detect_false_breakout(self, df, support_levels, resistance_levels):
        """
        Detect false breakout patterns
        Returns: signal dict or None
        """
        if len(df) < 15:
            return None
        
        # Need at least some support/resistance levels
        if not support_levels and not resistance_levels:
            return None
        
        # Get recent candles
        recent_candles = df.tail(5)
        current_candle = df.iloc[-1]
        prev_candle = df.iloc[-2]
        
        signal = None
        
        # Check for BULLISH false breakout (below support then back above)
        if support_levels:
            nearest_support = min(support_levels, key=lambda x: abs(x - current_candle['Close']))
            
            # Previous candle broke below support
            broke_support = prev_candle['Low'] < nearest_support * 0.997
            
            # Current candle closed back above support
            back_above = current_candle['Close'] > nearest_support * 1.002
            
            # Current candle is bullish
            is_bullish = current_candle['Close'] > current_candle['Open']
            
            # Check if breakout had volume (sign of stop hunt)
            if len(df) >= 20:
                avg_volume = df['Volume'].tail(20).mean()
                breakout_volume = prev_candle['Volume']
                had_volume = breakout_volume > avg_volume * self.volume_multiplier
            else:
                had_volume = True
            
            if broke_support and back_above and is_bullish and had_volume:
                signal = {
                    'type': 'BUY',
                    'pattern_name': 'Bullish False Breakout',
                    'pattern_strength': 'Strong',
                    'fakeout_level': round(nearest_support, 2),
                    'confirmation': f"Failed breakdown at {nearest_support:.2f}, reversed bullish"
                }
                
                logger.info(f"✅ BULLISH False Breakout detected at support {nearest_support:.2f}")
        
        # Check for BEARISH false breakout (above resistance then back below)
        if resistance_levels and signal is None:  # Only if no bullish signal found
            nearest_resistance = min(resistance_levels, key=lambda x: abs(x - current_candle['Close']))
            
            # Previous candle broke above resistance
            broke_resistance = prev_candle['High'] > nearest_resistance * 1.003
            
            # Current candle closed back below resistance
            back_below = current_candle['Close'] < nearest_resistance * 0.998
            
            # Current candle is bearish
            is_bearish = current_candle['Close'] < current_candle['Open']
            
            # Check if breakout had volume
            if len(df) >= 20:
                avg_volume = df['Volume'].tail(20).mean()
                breakout_volume = prev_candle['Volume']
                had_volume = breakout_volume > avg_volume * self.volume_multiplier
            else:
                had_volume = True
            
            if broke_resistance and back_below and is_bearish and had_volume:
                signal = {
                    'type': 'SELL',
                    'pattern_name': 'Bearish False Breakout',
                    'pattern_strength': 'Strong',
                    'fakeout_level': round(nearest_resistance, 2),
                    'confirmation': f"Failed breakout at {nearest_resistance:.2f}, reversed bearish"
                }
                
                logger.info(f"✅ BEARISH False Breakout detected at resistance {nearest_resistance:.2f}")
        
        return signal
    
    @log_exceptions
    def validate_false_breakout(self, df, signal):
        """
        Validate the false breakout signal
        Returns: True if valid, False otherwise
        """
        if signal is None:
            return False
        
        current_candle = df.iloc[-1]
        
        # Check that current candle has a decent body (not a doji)
        candle_range = current_candle['High'] - current_candle['Low']
        body_size = abs(current_candle['Close'] - current_candle['Open'])
        
        if candle_range > 0:
            body_ratio = body_size / candle_range
            if body_ratio < 0.3:  # Body must be at least 30% of range
                logger.debug("False breakout rejected: Weak reversal candle")
                return False
        
        # Check that we're not too far from the fakeout level
        distance_from_level = abs(current_candle['Close'] - signal['fakeout_level']) / signal['fakeout_level']
        if distance_from_level > 0.01:  # More than 1% away
            logger.debug("False breakout rejected: Too far from level")
            return False
        
        return True
