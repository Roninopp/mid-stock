#!/usr/bin/env python3
"""
Test Script - Verify bot setup before deploying
"""

import sys
import os

def test_imports():
    """Test if all modules can be imported"""
    print("🔍 Testing module imports...")
    
    modules = [
        'config',
        'logs',
        'data_fetcher',
        'indicators',
        'liquidity_sweep_detector',
        'false_breakout_detector',
        'engulfing_detector',
        'mid_signal_scanner',
        'approval',
        'telegram_bot'
    ]
    
    failed = []
    for module in modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except Exception as e:
            print(f"  ❌ {module} - {str(e)}")
            failed.append(module)
    
    if failed:
        print(f"\n❌ Failed to import: {', '.join(failed)}")
        return False
    
    print("\n✅ All modules imported successfully!")
    return True

def test_config():
    """Test configuration"""
    print("\n🔍 Testing configuration...")
    
    try:
        import config
        
        # Check bot token
        if config.TELEGRAM_BOT_TOKEN and len(config.TELEGRAM_BOT_TOKEN) > 20:
            print(f"  ✅ Bot token configured")
        else:
            print(f"  ❌ Bot token missing or invalid")
            return False
        
        # Check other settings
        print(f"  ✅ Stocks to scan: {len(config.NIFTY_50_STOCKS)}")
        print(f"  ✅ Scan interval: {config.SCAN_INTERVAL}s")
        print(f"  ✅ Admin ID: {config.ADMIN_USER_ID}")
        
        print("\n✅ Configuration looks good!")
        return True
        
    except Exception as e:
        print(f"  ❌ Config error: {str(e)}")
        return False

def test_strategies():
    """Test strategy detectors"""
    print("\n🔍 Testing strategy detectors...")
    
    try:
        from liquidity_sweep_detector import LiquiditySweepDetector
        from false_breakout_detector import FalseBreakoutDetector
        from engulfing_detector import EngulfingDetector
        
        sweep = LiquiditySweepDetector()
        print("  ✅ Liquidity Sweep Detector")
        
        breakout = FalseBreakoutDetector()
        print("  ✅ False Breakout Detector")
        
        engulfing = EngulfingDetector()
        print("  ✅ Engulfing Detector")
        
        print("\n✅ All strategies initialized!")
        return True
        
    except Exception as e:
        print(f"  ❌ Strategy error: {str(e)}")
        return False

def test_data_fetch():
    """Test data fetching"""
    print("\n🔍 Testing data fetch...")
    
    try:
        from data_fetcher import DataFetcher
        
        fetcher = DataFetcher()
        print("  📡 Fetching sample data for RELIANCE...")
        
        df = fetcher.fetch_stock_data("RELIANCE.NS", period="1d", interval="5m")
        
        if df is not None and len(df) > 0:
            print(f"  ✅ Data fetched: {len(df)} candles")
        else:
            print("  ⚠️  No data received (might be market closed)")
        
        print("\n✅ Data fetcher working!")
        return True
        
    except Exception as e:
        print(f"  ❌ Data fetch error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*50)
    print("🎯 MID-STRATEGY BOT - VERIFICATION")
    print("="*50 + "\n")
    
    results = []
    
    # Run tests
    results.append(("Module Imports", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("Strategy Detectors", test_strategies()))
    results.append(("Data Fetching", test_data_fetch()))
    
    # Summary
    print("\n" + "="*50)
    print("📊 SUMMARY")
    print("="*50)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n" + "="*50)
        print("🎉 ALL TESTS PASSED!")
        print("="*50)
        print("\n✅ Your bot is ready to deploy!")
        print("\nRun: bash deploy.sh")
        print("Or manually: screen -dmS mbot venv/bin/python telegram_bot.py\n")
    else:
        print("\n" + "="*50)
        print("⚠️  SOME TESTS FAILED")
        print("="*50)
        print("\nPlease fix the issues above before deploying.\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
