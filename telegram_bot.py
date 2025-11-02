"""
Mid-Strategy Telegram Bot
Sends trading signals for: Liquidity Sweep, False Breakout, Engulfing
"""

import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode
from datetime import datetime
import traceback

from mid_signal_scanner import MidStrategyScanner
from data_fetcher import DataFetcher
from logs import logger, performance_tracker
import config
from approval import add_user, is_user_approved

class MidStrategyBot:
    def __init__(self):
        """Initialize the bot"""
        self.scanner = MidStrategyScanner()
        self.data_fetcher = DataFetcher()
        self.is_running = False
        self.application = None
        self.chat_id = config.TELEGRAM_CHAT_ID
        
        logger.info("🤖 Mid-Strategy Bot initialized")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        
        if not is_user_approved(user_id):
            logger.info(f"Unapproved user {user_id} tried to start the bot")
            await update.message.reply_text(
                "❌ You need approval to use this bot.\n"
                "Contact @DushmanXRoninn for access."
            )
            return
        
        welcome_message = """
🎯 *Mid-Strategy Trading Bot*

This bot provides *frequent trading setups* with good win rates!

*Strategies:*
✅ Liquidity Sweep - Long wick rejections
✅ False Breakout - Fakeouts at key levels  
✅ Engulfing - Strong reversals at S/R

*Expected: 4-8 signals per day*
*Win Rate: 60-65%*

*Commands:*
/autotrade on - Start auto-scanning
/autotrade off - Stop scanning
/status - Check bot status
/scan - Manual scan
/logs - View recent activity
/help - Show this message

*Ready to trade!* 🚀
        """
        await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)
        logger.info(f"Bot started by user: {user_id}")
    
    async def adduser_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /adduser command (Admin only)"""
        admin_id = update.effective_user.id
        
        if admin_id != config.ADMIN_USER_ID:
            await update.message.reply_text("❌ Admin only command")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /adduser [user_id]")
            return
        
        try:
            user_id_to_add = int(context.args[0])
            if add_user(user_id_to_add):
                await update.message.reply_text(f"✅ User {user_id_to_add} approved!")
            else:
                await update.message.reply_text(f"⚠️ User already approved")
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID")
    
    async def autotrade_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /autotrade on/off"""
        user_id = update.effective_user.id
        if not is_user_approved(user_id):
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /autotrade on OR /autotrade off")
            return
        
        command = context.args[0].lower()
        
        if command == 'on':
            if self.is_running:
                await update.message.reply_text("✅ Already running!")
            else:
                self.is_running = True
                await update.message.reply_text(
                    "🚀 *Mid-Strategy Bot STARTED!*\n\n"
                    "🔍 Scanning every 30 seconds\n"
                    "📊 Looking for: Liquidity Sweeps, False Breakouts, Engulfing\n"
                    "⚡ Expect 4-8 signals per day",
                    parse_mode=ParseMode.MARKDOWN
                )
                logger.info("Auto-trading started")
                asyncio.create_task(self.trading_loop())
        
        elif command == 'off':
            if not self.is_running:
                await update.message.reply_text("⚠️ Already stopped!")
            else:
                self.is_running = False
                await update.message.reply_text("🛑 *Bot STOPPED!*", parse_mode=ParseMode.MARKDOWN)
                logger.info("Auto-trading stopped")
        else:
            await update.message.reply_text("❌ Use: /autotrade on OR /autotrade off")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status"""
        user_id = update.effective_user.id
        if not is_user_approved(user_id):
            return
        
        stats = performance_tracker.get_stats()
        market_status, market_msg = self.data_fetcher.get_market_status()
        
        status_emoji = "🟢" if self.is_running else "🔴"
        market_emoji = "🟢" if market_status else "🔴"
        
        status_message = f"""
📊 *BOT STATUS*

{status_emoji} Auto-trading: {'RUNNING' if self.is_running else 'STOPPED'}
{market_emoji} Market: {market_msg}

📈 *Performance Stats:*
• Scans completed: {stats['scans_completed']}
• Signals sent: {stats['total_signals']}
• Avg scan time: {stats['avg_scan_time']:.2f}s
• API calls: {stats['total_api_calls']}
• Errors: {stats['total_errors']}

⏰ Current time: {datetime.now().strftime('%H:%M:%S')}
📅 Date: {datetime.now().strftime('%d %b %Y')}
        """
        
        await update.message.reply_text(status_message, parse_mode=ParseMode.MARKDOWN)
    
    async def logs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /logs"""
        user_id = update.effective_user.id
        if not is_user_approved(user_id):
            return
        
        recent_logs = logger.get_recent_logs(count=15)
        
        if not recent_logs:
            await update.message.reply_text("📝 No logs available")
            return
        
        logs_message = "📝 *Recent Logs:*\n\n" + "\n".join(recent_logs[-15:])
        
        if len(logs_message) > 4000:
            logs_message = logs_message[-4000:]
        
        await update.message.reply_text(logs_message, parse_mode=ParseMode.MARKDOWN)
    
    async def scan_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /scan - manual scan"""
        user_id = update.effective_user.id
        if not is_user_approved(user_id):
            return
        
        await update.message.reply_text("🔍 Starting scan...")
        
        signals = self.scanner.scan_all_stocks()
        
        if signals:
            await update.message.reply_text(f"✅ Found {len(signals)} opportunities!")
            for signal in signals:
                await self.send_signal(signal)
        else:
            await update.message.reply_text("❌ No opportunities found this scan")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help"""
        user_id = update.effective_user.id
        if not is_user_approved(user_id):
            return
        
        help_message = """
📚 *MID-STRATEGY BOT HELP*

*Strategies Used:*
1️⃣ *Liquidity Sweep* - Price sweeps a level with long wick then reverses
2️⃣ *False Breakout* - Price breaks S/R then reverses back
3️⃣ *Engulfing* - Strong engulfing candles at key levels

*Commands:*
/start - Initialize bot
/autotrade on - Start scanning
/autotrade off - Stop scanning
/status - View stats
/scan - Manual scan
/logs - Recent activity
/help - This message

*Trading Tips:*
• Win Rate: ~60-65%
• Use proper position sizing (1-2% risk)
• Set stop loss immediately
• Take partial profits at Target 1
• Let rest run to Target 2

Good luck! 📈
        """
        await update.message.reply_text(help_message, parse_mode=ParseMode.MARKDOWN)
    
    async def send_signal(self, signal):
        """Send trading signal to Telegram"""
        try:
            signal_emoji = "🟢" if signal['signal_type'] == 'BUY' else "🔴"
            
            message = f"""
{signal_emoji} *{signal['signal_type']} - {signal['symbol']}*

📊 *Strategy:* {signal['pattern_name']}
{signal['pattern_details']}

💰 *Entry:* ₹{signal['entry_price']}
🛑 *Stop Loss:* ₹{signal['stop_loss']}
🎯 *Target 1:* ₹{signal['target_1']}
🎯 *Target 2:* ₹{signal['target_2']}

📈 *Risk:Reward:* 1:{signal['risk_reward']}
📊 *RSI:* {signal['rsi_value']}

✅ *Confirmations:* {', '.join(signal['confirmations']) if signal['confirmations'] else 'Pattern only'}

⏰ {signal['timestamp'].strftime('%I:%M %p')}
            """
            
            await self.application.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.info(f"✅ Signal sent: {signal['symbol']}")
            
        except Exception as e:
            logger.error(f"Error sending signal: {str(e)}")
    
    async def trading_loop(self):
        """Main trading loop"""
        logger.info("🔄 Trading loop started")
        
        while self.is_running:
            try:
                market_open, market_msg = self.data_fetcher.get_market_status()
                
                if not market_open:
                    logger.info(f"Market closed: {market_msg}")
                    await asyncio.sleep(300)
                    continue
                
                signals = self.scanner.scan_all_stocks()
                
                if signals:
                    for signal in signals:
                        await self.send_signal(signal)
                        await asyncio.sleep(2)
                
                await asyncio.sleep(config.SCAN_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in trading loop: {str(e)}")
                await asyncio.sleep(60)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")
    
    def run(self):
        """Start the bot"""
        logger.info("🚀 Starting Mid-Strategy Telegram Bot...")
        
        self.application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
        
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("adduser", self.adduser_command))
        self.application.add_handler(CommandHandler("autotrade", self.autotrade_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("logs", self.logs_command))
        self.application.add_handler(CommandHandler("scan", self.scan_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_error_handler(self.error_handler)
        
        logger.info("✅ Bot ready! Waiting for commands...")
        
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    bot = MidStrategyBot()
    bot.run()
