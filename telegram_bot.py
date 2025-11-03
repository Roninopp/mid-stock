"""
ADD THIS NEW COMMAND to your telegram_bot.py
Put it after the help_command function
"""

async def diagnostic_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /diagnostic - Show why signals are rejected"""
    user_id = update.effective_user.id
    if not is_user_approved(user_id):
        return
    
    await update.message.reply_text("🔍 Running diagnostic scan...")
    
    # Run scan
    signals = self.scanner.scan_all_stocks()
    
    # Get rejection stats
    stats = self.scanner.get_rejection_stats()
    
    # Build diagnostic message
    message = f"""
🔬 *DIAGNOSTIC REPORT*

📊 *Scan Results:*
• Total scanned: {stats['total_scanned']}
• Signals found: {len(signals)}
• No data: {stats['no_data']}
• Insufficient candles: {stats['insufficient_candles']}

🔍 *Pattern Detection:*
• Sweeps detected: {stats['sweep_detected']}
  └─ Rejected: {stats['sweep_rejected']}
• Breakouts detected: {stats['breakout_detected']}
  └─ Rejected: {stats['breakout_rejected']}
• Engulfing detected: {stats['engulfing_detected']}
  └─ Rejected: {stats['engulfing_rejected']}

❌ *Rejection Reasons:*
• Low RR ratio: {stats['low_rr_ratio']}

💡 *Suggestions:*
"""
    
    # Add suggestions based on stats
    if stats['sweep_detected'] > 0 and len(signals) == 0:
        message += "\n• Patterns detected but rejected"
        message += "\n• Try relaxing filters in config.py"
    
    if stats['no_data'] > 10:
        message += "\n• High data fetch failures"
        message += "\n• Check API rate limits"
    
    if stats['sweep_detected'] == 0 and stats['breakout_detected'] == 0:
        message += "\n• No patterns detected at all"
        message += "\n• Market might be too quiet"
        message += "\n• Or filters are too strict"
    
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

# ============================================
# ALSO ADD THIS to the run() method:
# ============================================
"""
In the run() method, add this line:

self.application.add_handler(CommandHandler("diagnostic", self.diagnostic_command))

So it looks like:
self.application.add_handler(CommandHandler("start", self.start_command))
self.application.add_handler(CommandHandler("diagnostic", self.diagnostic_command))  # <-- ADD THIS
self.application.add_handler(CommandHandler("adduser", self.adduser_command))
...
"""
