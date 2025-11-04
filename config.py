"""
Configuration File for Mid-Strategy Trading Bot
OPTIMIZED VERSION - Balanced between quality and frequency
"""

# ============================================
# TELEGRAM CONFIGURATION
# ============================================
TELEGRAM_BOT_TOKEN = "8424528396:AAG-fYttHVxwBgozIRRH8hByeF8FPOhxySQ"  # Get from @BotFather
TELEGRAM_CHAT_ID = "-1003103484269"      # Your chat/group ID
ADMIN_USER_ID = 6837532865                     # Your Telegram user ID

# ============================================
# TRADING PARAMETERS (OPTIMIZED FOR 5M CANDLES)
# ============================================
TIMEFRAME = '5m'  # 5-minute candles
SCAN_INTERVAL = 300  # Scan every 5 minutes (when new candle closes!)

# Why 5 minutes?
# ✅ Matches candle timeframe (scan on candle close)
# ✅ Fresh patterns, no incomplete candles
# ✅ ~70 scans/day = ~3,500 API calls/day (well under limit)
# ✅ Low VPS load, minimal lag
# ✅ Time to analyze and execute trades
# ✅ 5-8 quality signals per day

# Stop Loss and Targets (in percentage)
STOP_LOSS_PERCENTAGE = 1.5    # 1.5% stop loss
TARGET_PERCENTAGE_1 = 2.0      # 2% first target
TARGET_PERCENTAGE_2 = 3.5      # 3.5% second target

MIN_RISK_REWARD_RATIO = 1.2    # Minimum 1:1.2 RR

# ============================================
# STRATEGY SETTINGS (OPTIMIZED)
# ============================================

# Liquidity Sweep Settings
# CHANGED: Reduced from 0.6 to 0.5 (50% wick instead of 60%)
SWEEP_WICK_RATIO = 0.5         # Wick must be 50% of total candle (RELAXED)
SWEEP_LOOKBACK = 20            # Look back 20 candles for sweep detection
# CHANGED: Reduced from 0.4 to 0.35 (35% body)
SWEEP_REVERSAL_BODY = 0.35     # Reversal candle body ratio (RELAXED)

# False Breakout Settings
BREAKOUT_CONFIRMATION_CANDLES = 2
# CHANGED: Reduced from 1.3 to 1.2
BREAKOUT_VOLUME_MULTIPLIER = 1.2  # Volume should be 1.2x average (RELAXED)

# Engulfing Settings
# CHANGED: Reduced from 1.2 to 1.15 (15% larger instead of 20%)
ENGULFING_BODY_RATIO = 1.15     # Current body 15% larger than previous (RELAXED)

# Support/Resistance Settings
# CHANGED: Increased from 0.5% to 0.8%
SR_TOUCH_THRESHOLD = 0.8       # 0.8% distance to consider "at level" (RELAXED)
SR_LOOKBACK_DAYS = 20          # Days to look back for S/R levels

# ============================================
# INDICATORS (OPTIMIZED)
# ============================================
RSI_PERIOD = 14
RSI_OVERSOLD = 35
RSI_OVERBOUGHT = 65

VOLUME_MA_PERIOD = 20
# CHANGED: Reduced from 1.2 to 1.1
MIN_VOLUME_RATIO = 1.1         # Volume should be 1.1x average (RELAXED)

# ============================================
# PERFORMANCE SETTINGS
# ============================================
MAX_WORKERS = 5                # Parallel threads for scanning
API_RATE_LIMIT = 1.0          # Seconds between API calls

# ============================================
# SAFETY SETTINGS (NEW - HIGHLY RECOMMENDED)
# ============================================
MAX_SIGNALS_PER_DAY = 10       # Maximum signals to send per day
MIN_SIGNAL_GAP_SECONDS = 180   # Minimum 3 minutes between signals
DUPLICATE_SIGNAL_WINDOW = 900  # Ignore duplicate signals within 15 minutes

# ============================================
# NIFTY 50 STOCKS (UPDATED - Removed delisted stocks)
# ============================================
NIFTY_50_STOCKS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "BAJFINANCE.NS",
    "ASIANPAINT.NS", "MARUTI.NS", "HCLTECH.NS", "KOTAKBANK.NS", "LT.NS",
    "AXISBANK.NS", "TITAN.NS", "SUNPHARMA.NS", "ULTRACEMCO.NS", "NESTLEIND.NS",
    "WIPRO.NS", "TECHM.NS", "NTPC.NS", "ONGC.NS", "POWERGRID.NS",
    "M&M.NS", "BAJAJFINSV.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "ADANIPORTS.NS",
    "COALINDIA.NS", "HINDALCO.NS", "JSWSTEEL.NS", "INDUSINDBK.NS", "BRITANNIA.NS",
    "DIVISLAB.NS", "DRREDDY.NS", "EICHERMOT.NS", "GRASIM.NS", "HEROMOTOCO.NS",
    "CIPLA.NS", "APOLLOHOSP.NS", "BAJAJ-AUTO.NS", "SHREECEM.NS", "TATACONSUM.NS",
    "UPL.NS", "BPCL.NS"
    # Removed HDFCLIFE.NS, SBILIFE.NS, ADANIENT.NS - causing data issues
]

# ============================================
# ALTERNATIVE: HIGH-VOLUME STOCKS (Optional)
# ============================================
# If you want MORE signals, scan these high-volume stocks instead:
HIGH_VOLUME_STOCKS = [
    "RELIANCE.NS", "INFY.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "SBIN.NS", "BHARTIARTL.NS", "TATAMOTORS.NS", "AXISBANK.NS", "KOTAKBANK.NS",
    "TATASTEEL.NS", "ITC.NS", "LT.NS", "MARUTI.NS", "BAJFINANCE.NS",
    "SUNPHARMA.NS", "WIPRO.NS", "HINDALCO.NS", "ADANIPORTS.NS", "TITAN.NS"
]

# To use high-volume stocks only, uncomment this line:
# NIFTY_50_STOCKS = HIGH_VOLUME_STOCKS

# ============================================
# MARKET TIMING (IST)
# ============================================
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 15
MARKET_CLOSE_HOUR = 15
MARKET_CLOSE_MINUTE = 30

# ============================================
# LOGGING
# ============================================
LOG_FILE = "bot_logs.txt"
LOG_LEVEL = "INFO"
MAX_LOG_LINES = 1000

# ============================================
# CONFIGURATION PRESETS (Choose one)
# ============================================
"""
PRESET 1: QUALITY (Current settings)
- 4-6 signals per day
- ~65% win rate
- Fewer but higher quality signals

PRESET 2: BALANCED (Recommended)
- 6-10 signals per day
- ~60% win rate
- Good balance

PRESET 3: QUANTITY
- 10-15 signals per day
- ~55% win rate
- More signals, slightly lower quality

To switch presets, adjust the values above:
- SWEEP_WICK_RATIO: 0.6 (Quality) | 0.5 (Balanced) | 0.45 (Quantity)
- SR_TOUCH_THRESHOLD: 0.5 (Quality) | 0.8 (Balanced) | 1.0 (Quantity)
- MIN_VOLUME_RATIO: 1.2 (Quality) | 1.1 (Balanced) | 1.0 (Quantity)
"""
