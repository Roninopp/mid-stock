"""
Engulfing Pattern Detector Module
Detects engulfing patterns at key support/resistance levels
"""

import pandas as pd
import numpy as np
from logs import logger, log_exceptions
import config

class EngulfingDetector:
    def __init__(self):
        """Initialize engulfing detector"""
        self.sr_threshold = config.SR_TOUCH_THRESHOLD / 100
        
    @log_exceptions
    def detect_engulfing(self, df, support_levels, resistance_levels):
        """
        Detect engulfing patterns at key levels
        Returns: signal dict or None
        """
        if len(df) < 3:
            return None
        
        # Get last two candles
        prev_candle = df.iloc[-2]
        current_candle = df.iloc[-1]
        
        # Calculate bodies
        prev_body = abs(prev_candle['Close'] - prev_candle['Open'])
        current_body = abs(current_candle['Close'] - current_candle['Open'])
        current_range = current_candle['High'] - current_candle['Low']
        
        # Current candle must have a strong body (not a doji)
        if current_range > 0:
            body_ratio = current_body / current_range
            if body_ratio < 0.5:  # Body must be at least 50% of range
                return None
        
        signal = None
        current_price = current_candle['Close']
        
        # BULLISH ENGULFING (BUY Signal)
        prev_bearish = prev_candle['Close'] < prev_candle['Open']
        current_bullish = current_candle['Close'] > current_candle['Open']
        engulfs = (current_candle['Open'] <= prev_candle['Close'] and 
                   current_candle['Close'] >= prev_candle['Open'])
        strong_body = current_body > prev_body * 1.2  # Current body 20% larger
        
        if prev_bearish and current_bullish and engulfs and strong_body:
            # Check if near support level
            near_support = False
            support_level = None
            
            if support_levels:
                for level in support_levels:
                    distance = abs(current_price - level) / level
                    if distance <= self.sr_threshold:
                        near_support = True
                        support_level = level
                        break
            
            if near_support:
                signal = {
                    'type': 'BUY',
                    'pattern_name': 'Bullish Engulfing',
                    'pattern_strength': 'Strong',
                    'key_level': round(support_level, 2),
                    'level_type': 'support',
                    'confirmation': f"Bullish engulfing at support {support_level:.2f}"
                }
                
                logger.info(f"✅ BULLISH Engulfing detected at support {support_level:.2f}")
        
        # BEARISH ENGULFING (SELL Signal)
        prev_bullish = prev_candle['Close'] > prev_candle['Open']
        current_bearish = current_candle['Close'] < current_candle['Open']
        engulfs = (current_candle['Open'] >= prev_candle['Close'] and 
                   current_candle['Close'] <= prev_candle['Open'])
        strong_body = current_body > prev_body * 1.2
        
        if prev_bullish and current_bearish and engulfs and strong_body and signal is None:
            # Check if near resistance level
            near_resistance = False
            resistance_level = None
            
            if resistance_levels:
                for level in resistance_levels:
                    distance = abs(current_price - level) / level
                    if distance <= self.sr_threshold:
                        near_resistance = True
                        resistance_level = level
                        break
            
            if near_resistance:
                signal = {
                    'type': 'SELL',
                    'pattern_name': 'Bearish Engulfing',
                    'pattern_strength': 'Strong',
                    'key_level': round(resistance_level, 2),
                    'level_type': 'resistance',
                    'confirmation': f"Bearish engulfing at resistance {resistance_level:.2f}"
                }
                
                logger.info(f"✅ BEARISH Engulfing detected at resistance {resistance_level:.2f}")
        
        return signal
    
    @log_exceptions
    def validate_engulfing(self, df, signal):
        """
        Validate the engulfing pattern
        Returns: True if valid, False otherwise
        """
        if signal is None:
            return False
        
        current_candle = df.iloc[-1]
        
        # Check volume confirmation (optional but good)
        if len(df) >= 20:
            avg_volume = df['Volume'].tail(20).mean()
            current_volume = current_candle['Volume']
            
            # Volume should be at least average (showing conviction)
            if current_volume < avg_volume * 0.9:
                logger.debug("Engulfing rejected: Low volume")
                return False
        
        # Make sure we're still close to the key level
        distance = abs(current_candle['Close'] - signal['key_level']) / signal['key_level']
        if distance > 0.008:  # More than 0.8% away
            logger.debug("Engulfing rejected: Moved too far from level")
            return False
        
        return True
