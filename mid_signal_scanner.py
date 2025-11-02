"""
Mid-Strategy Signal Scanner
Combines: Liquidity Sweep + False Breakout + Engulfing patterns
"""

import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import time

from data_fetcher import DataFetcher
from liquidity_sweep_detector import LiquiditySweepDetector
from false_breakout_detector import FalseBreakoutDetector
from engulfing_detector import EngulfingDetector
from indicators import IndicatorAnalyzer
from logs import logger, log_exceptions, performance_tracker
import config

class MidStrategyScanner:
    def __init__(self):
        """Initialize all strategy detectors"""
        self.data_fetcher = DataFetcher()
        self.liquidity_detector = LiquiditySweepDetector()
        self.breakout_detector = FalseBreakoutDetector()
        self.engulfing_detector = EngulfingDetector()
        self.indicator_analyzer = IndicatorAnalyzer()
        
        self.stocks = config.NIFTY_50_STOCKS
        self.scan_interval = config.SCAN_INTERVAL
        self.max_workers = config.MAX_WORKERS
        
        logger.info(f"🚀 Mid-Strategy Scanner initialized with {len(self.stocks)} stocks")
        logger.info("📊 Strategies: Liquidity Sweep, False Breakout, Engulfing at Levels")
    
    @log_exceptions
    def scan_stock(self, symbol):
        """
        Scan a single stock for ALL three strategies
        Returns: signal dict if found, None otherwise
        """
        try:
            # Fetch data
            df = self.data_fetcher.fetch_stock_data(
                symbol, 
                period='5d', 
                interval=config.TIMEFRAME
            )
            
            if df is None or len(df) < 30:
                return None
            
            # Calculate support and resistance (needed for multiple strategies)
            support_levels, resistance_levels = self.indicator_analyzer.calculate_support_resistance(df)
            
            current_price = df['Close'].iloc[-1]
            signal = None
            
            # STRATEGY 1: Liquidity Sweep (PRIORITY)
            sweep_signal = self.liquidity_detector.detect_sweep(df)
            if sweep_signal and self.liquidity_detector.validate_sweep(df, sweep_signal):
                signal = self._build_signal(df, symbol, sweep_signal, support_levels, resistance_levels)
                if signal:
                    logger.info(f"💎 Liquidity Sweep signal found: {symbol}")
                    return signal
            
            # STRATEGY 2: False Breakout
            breakout_signal = self.breakout_detector.detect_false_breakout(df, support_levels, resistance_levels)
            if breakout_signal and self.breakout_detector.validate_false_breakout(df, breakout_signal):
                signal = self._build_signal(df, symbol, breakout_signal, support_levels, resistance_levels)
                if signal:
                    logger.info(f"💎 False Breakout signal found: {symbol}")
                    return signal
            
            # STRATEGY 3: Engulfing at Levels
            engulfing_signal = self.engulfing_detector.detect_engulfing(df, support_levels, resistance_levels)
            if engulfing_signal and self.engulfing_detector.validate_engulfing(df, engulfing_signal):
                signal = self._build_signal(df, symbol, engulfing_signal, support_levels, resistance_levels)
                if signal:
                    logger.info(f"💎 Engulfing signal found: {symbol}")
                    return signal
            
            return None
            
        except Exception as e:
            logger.error(f"Error scanning {symbol}: {str(e)}")
            performance_tracker.increment_errors()
            return None
    
    def _build_signal(self, df, symbol, pattern_signal, support_levels, resistance_levels):
        """
        Build complete signal with entry, SL, targets
        """
        try:
            current_price = df['Close'].iloc[-1]
            signal_type = pattern_signal['type']
            
            # Calculate entry, stop loss, and targets
            entry_price = current_price
            
            if signal_type == 'BUY':
                stop_loss = entry_price * (1 - config.STOP_LOSS_PERCENTAGE / 100)
                target_1 = entry_price * (1 + config.TARGET_PERCENTAGE_1 / 100)
                target_2 = entry_price * (1 + config.TARGET_PERCENTAGE_2 / 100)
            else:  # SELL
                stop_loss = entry_price * (1 + config.STOP_LOSS_PERCENTAGE / 100)
                target_1 = entry_price * (1 - config.TARGET_PERCENTAGE_1 / 100)
                target_2 = entry_price * (1 - config.TARGET_PERCENTAGE_2 / 100)
            
            # Calculate risk:reward ratio
            risk = abs(entry_price - stop_loss)
            reward = abs(target_1 - entry_price)
            rr_ratio = reward / risk if risk > 0 else 0
            
            # Check minimum RR ratio
            if rr_ratio < config.MIN_RISK_REWARD_RATIO:
                logger.debug(f"Signal rejected for {symbol}: RR {rr_ratio:.2f} too low")
                return None
            
            # Get volume confirmation
            volume_confirmed, volume_ratio = self.indicator_analyzer.check_volume_confirmation(df)
            
            # Calculate RSI (optional for mid-strategy)
            rsi_values = self.indicator_analyzer.calculate_rsi(df)
            current_rsi = rsi_values.iloc[-1] if len(rsi_values) > 0 else 50
            
            # Build final signal
            signal = {
                'symbol': symbol.replace('.NS', ''),
                'signal_type': signal_type,
                'pattern_name': pattern_signal['pattern_name'],
                'pattern_strength': pattern_signal['pattern_strength'],
                'entry_price': round(entry_price, 2),
                'stop_loss': round(stop_loss, 2),
                'target_1': round(target_1, 2),
                'target_2': round(target_2, 2),
                'risk_reward': round(rr_ratio, 2),
                'rsi_value': round(current_rsi, 2),
                'volume_ratio': round(volume_ratio, 2),
                'volume_confirmed': volume_confirmed,
                'support_levels': [round(l, 2) for l in support_levels[:3]],
                'resistance_levels': [round(l, 2) for l in resistance_levels[:3]],
                'timestamp': datetime.now(),
                'dataframe': df,
                'pattern_details': pattern_signal.get('confirmation', '')
            }
            
            # Build confirmation list
            confirmations = []
            if volume_confirmed:
                confirmations.append(f"Volume {volume_ratio:.1f}x")
            if signal_type == 'BUY' and current_rsi < 45:
                confirmations.append(f"RSI {current_rsi:.0f}")
            elif signal_type == 'SELL' and current_rsi > 55:
                confirmations.append(f"RSI {current_rsi:.0f}")
            
            signal['confirmations'] = confirmations
            
            return signal
            
        except Exception as e:
            logger.error(f"Error building signal for {symbol}: {str(e)}")
            return None
    
    @log_exceptions
    def scan_all_stocks(self):
        """
        Scan all stocks in parallel for ALL strategies
        Returns: list of signals
        """
        start_time = time.time()
        signals = []
        
        logger.info(f"🔍 Scanning {len(self.stocks)} stocks...")
        
        # Parallel scanning
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_stock = {
                executor.submit(self.scan_stock, stock): stock 
                for stock in self.stocks
            }
            
            for future in as_completed(future_to_stock):
                stock = future_to_stock[future]
                try:
                    signal = future.result()
                    if signal:
                        signals.append(signal)
                        performance_tracker.increment_signals()
                except Exception as e:
                    logger.error(f"Exception scanning {stock}: {str(e)}")
        
        # Record scan time
        duration = time.time() - start_time
        performance_tracker.record_scan_time(duration)
        
        logger.info(f"✅ Scan complete in {duration:.2f}s | Signals found: {len(signals)}")
        
        return signals
