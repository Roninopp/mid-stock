"""
Liquidity Sweep Detector Module
Detects liquidity sweeps (long wicks indicating stop hunts)
"""

import pandas as pd
import numpy as np
from logs import logger, log_exceptions
import config

class LiquiditySweepDetector:
    def __init__(self):
        """Initialize liquidity sweep detector"""
        self.wick_ratio = config.SWEEP_WICK_RATIO
        self.lookback = config.SWEEP_LOOKBACK
        self.reversal_body_ratio = config.SWEEP_REVERSAL_BODY
    
    @log_exceptions
    def detect_sweep(self, df):
        """
        Detect liquidity sweep patterns
        Returns: signal dict or None
        """
        if len(df) < self.lookback:
            return None
        
        # Get current and previous candles
        current_candle = df.iloc[-1]
        prev_candle = df.iloc[-2]
        
        # Calculate candle components
        candle_range = current_candle['High'] - current_candle['Low']
        body_size = abs(current_candle['Close'] - current_candle['Open'])
        
        if candle_range == 0:
            return None
        
        # Calculate wick sizes
        if current_candle['Close'] > current_candle['Open']:  # Bullish candle
            upper_wick = current_candle['High'] - current_candle['Close']
            lower_wick = current_candle['Open'] - current_candle['Low']
        else:  # Bearish candle
            upper_wick = current_candle['High'] - current_candle['Open']
            lower_wick = current_candle['Close'] - current_candle['Low']
        
        signal = None
        
        # BULLISH SWEEP (Long lower wick, closes up)
        # Price swept below recent lows then closed higher
        lower_wick_ratio = lower_wick / candle_range
        is_bullish_close = current_candle['Close'] > current_candle['Open']
        has_body = body_size / candle_range >= self.reversal_body_ratio
        
        if (lower_wick_ratio >= self.wick_ratio and 
            is_bullish_close and 
            has_body):
            
            # Check if swept below recent lows
            recent_lows = df['Low'].tail(self.lookback).iloc[:-1]  # Exclude current
            swept_recent_low = current_candle['Low'] < recent_lows.min()
            
            if swept_recent_low:
                sweep_level = round(recent_lows.min(), 2)
                
                signal = {
                    'type': 'BUY',
                    'pattern_name': 'Bullish Liquidity Sweep',
                    'pattern_strength': 'Strong',
                    'sweep_level': sweep_level,
                    'wick_ratio': round(lower_wick_ratio * 100, 1),
                    'confirmation': f"Swept below {sweep_level}, closed bullish with {lower_wick_ratio*100:.0f}% wick"
                }
                
                logger.info(f"✅ BULLISH Liquidity Sweep detected - Wick: {lower_wick_ratio*100:.1f}%")
        
        # BEARISH SWEEP (Long upper wick, closes down)
        # Price swept above recent highs then closed lower
        upper_wick_ratio = upper_wick / candle_range
        is_bearish_close = current_candle['Close'] < current_candle['Open']
        has_body = body_size / candle_range >= self.reversal_body_ratio
        
        if (upper_wick_ratio >= self.wick_ratio and 
            is_bearish_close and 
            has_body and 
            signal is None):  # Only if no bullish signal
            
            # Check if swept above recent highs
            recent_highs = df['High'].tail(self.lookback).iloc[:-1]
            swept_recent_high = current_candle['High'] > recent_highs.max()
            
            if swept_recent_high:
                sweep_level = round(recent_highs.max(), 2)
                
                signal = {
                    'type': 'SELL',
                    'pattern_name': 'Bearish Liquidity Sweep',
                    'pattern_strength': 'Strong',
                    'sweep_level': sweep_level,
                    'wick_ratio': round(upper_wick_ratio * 100, 1),
                    'confirmation': f"Swept above {sweep_level}, closed bearish with {upper_wick_ratio*100:.0f}% wick"
                }
                
                logger.info(f"✅ BEARISH Liquidity Sweep detected - Wick: {upper_wick_ratio*100:.1f}%")
        
        return signal
    
    @log_exceptions
    def validate_sweep(self, df, signal):
        """
        Validate the liquidity sweep signal
        Returns: True if valid, False otherwise
        """
        if signal is None:
            return False
        
        current_candle = df.iloc[-1]
        
        # Check volume confirmation (should be above average)
        if len(df) >= 20:
            avg_volume = df['Volume'].tail(20).mean()
            current_volume = current_candle['Volume']
            
            # Sweep should have decent volume
            if current_volume < avg_volume * 0.8:
                logger.debug("Sweep rejected: Low volume")
                return False
        
        # Check that price has moved away from sweep level
        # This confirms the rejection
        candle_range = current_candle['High'] - current_candle['Low']
        
        if signal['type'] == 'BUY':
            # For bullish sweep, close should be significantly above the low
            reversal_distance = current_candle['Close'] - current_candle['Low']
            if reversal_distance < candle_range * 0.4:
                logger.debug("Sweep rejected: Weak reversal")
                return False
        else:  # SELL
            # For bearish sweep, close should be significantly below the high
            reversal_distance = current_candle['High'] - current_candle['Close']
            if reversal_distance < candle_range * 0.4:
                logger.debug("Sweep rejected: Weak reversal")
                return False
        
        # Check RSI for confluence (optional but good)
        try:
            from indicators import IndicatorAnalyzer
            analyzer = IndicatorAnalyzer()
            rsi = analyzer.calculate_rsi(df)
            
            if len(rsi) > 0:
                current_rsi = rsi.iloc[-1]
                
                if signal['type'] == 'BUY' and current_rsi > 70:
                    logger.debug("Sweep rejected: RSI overbought")
                    return False
                elif signal['type'] == 'SELL' and current_rsi < 30:
                    logger.debug("Sweep rejected: RSI oversold")
                    return False
        except:
            pass  # RSI check is optional
        
        return True
