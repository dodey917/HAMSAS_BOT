import os
import logging
from telegram import Update, BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ContextTypes
)
from telegram.constants import ParseMode

print("="*60)
print("🤖 STARTING TELEGRAM PROTECTION BOT")
print("="*60)

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import our modules after logging is set up
try:
    from database import db
    from monitoring import ActivityMonitor
    from alert_system import AlertSystem
    from reporting import ReportingSystem  # NEW: Import reporting system
    import config
    print("✅ All modules imported successfully")
except ImportError as e:
    print(f"❌ Failed to import modules: {e}")
    exit(1)

class ProtectionBot:
    def __init__(self):
        print("\n🔨 Creating ProtectionBot instance...")
        self.config = config.Config()
        self.monitor = ActivityMonitor()
        self.alert_system = AlertSystem(self.config.BOT_TOKEN)
        self.reporting = None  # Will be initialized later when bot is available
        print("✅ ProtectionBot instance created")
    
    # ===== EXISTING COMMANDS (PRESERVED) =====
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send welcome message when the bot is started"""
        print("🎯 /start command received from user: {}".format(update.effective_user.id))
        
        welcome_text = """
🤖 <b>Community Protection Bot</b>

I help protect your Telegram communities from suspicious activities that could lead to bans.

<b>Features:</b>
• Monitor messages for spam and suspicious content
• Detect flooding and rate limiting violations
• Alert community owners about potential risks
• Track suspicious user activities

<b>Setup:</b>
Add me to your group/channel and make me an administrator with full permissions for complete protection.

<b>Available Commands:</b>
/start - Start the bot
/help - Show help information  
/stats - Get group statistics
/settings - Configure bot settings
/alerts - Manage alert preferences
/report - Report suspicious activity
/groupreport - Current group status

Developed with ❤️ for Telegram community safety.
        """
        try:
            await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML)
            print("✅ Welcome message sent successfully")
        except Exception as e:
            print("❌ Failed to send welcome message: {}".format(e))
    
    # ===== NEW COMMANDS =====
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send help information"""
        help_text = """
🆘 <b>HAMSAS Bot Help Guide</b>

🤖 <b>About Me:</b>
I'm an advanced security bot designed to protect your Telegram groups from various threats including spam, raids, and suspicious activities.

📋 <b>Available Commands:</b>

🔹 /start - Start the bot and see welcome message
🔹 /help - Show this help information  
🔹 /stats - Get group statistics and security overview
🔹 /settings - Configure bot settings and preferences
🔹 /alerts - Manage alert types and notification preferences
🔹 /report - Report suspicious activity to admins
🔹 /groupreport - Get current group status report

🛡️ <b>Security Features:</b>
• Suspicious keyword detection
• Mass joining monitoring
• User behavior analysis
• Spam pattern recognition
• Real-time alert system

⚙️ <b>Setup:</b>
Make me an admin with:
• Delete messages permission
• Ban users permission  
• Read messages permission

Need help? Contact my developer!
        """
        await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send group statistics"""
        chat_id = update.effective_chat.id
        
        try:
            # Get basic chat information
            chat = await context.bot.get_chat(chat_id)
            
            stats_text = f"""
📊 <b>Group Statistics - {chat.title}</b>

👥 <b>Members:</b> Loading...
🚨 <b>Activities Today:</b> 0
⚠️ <b>Alerts Today:</b> 0
🔍 <b>Suspicious Activities:</b> 0

📈 <b>Security Status:</b> 🔒 Protected
🕒 <b>Last Scan:</b> Just now

<i>More detailed analytics coming soon!</i>
            """
            await update.message.reply_text(stats_text, parse_mode=ParseMode.HTML)
            
        except Exception as e:
            await update.message.reply_text("❌ Could not fetch statistics. Make sure I'm an admin in this group.")
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Configure bot settings"""
        settings_text = """
⚙️ <b>Bot Settings</b>

🔧 <b>Available Settings:</b>

• <b>Alert Types:</b> Configure what triggers alerts
• <b>Sensitivity:</b> Adjust detection sensitivity  
• <b>Notification:</b> Set alert delivery methods
• <b>Language:</b> Choose preferred language

🛠️ <b>Quick Setup:</b>
Use /alerts to manage alert preferences

🔐 <b>Admin-only Features:</b>
• Auto-moderation rules
• Custom keyword lists
• User restriction settings

<i>Settings interface coming in next update!</i>
        """
        await update.message.reply_text(settings_text, parse_mode=ParseMode.HTML)
    
    async def alerts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manage alert preferences"""
        alerts_text = """
🚨 <b>Alert Management</b>

📢 <b>Alert Types Available:</b>

✅ <b>Suspicious Logins</b> - Unusual user activity
✅ <b>Mass Joining</b> - Multiple users joining rapidly  
✅ <b>Spam Detection</b> - Suspected spam messages
✅ <b>Admin Actions</b> - Important moderation events
✅ <b>Threat Detection</b> - Security threats

🔔 <b>Notification Options:</b>
• In-group alerts
• Admin mentions
• Silent mode
• Summary reports

⚡ <b>Quick Actions:</b>
• Enable/disable specific alerts
• Set alert sensitivity levels
• Configure mute durations

<i>Alert management interface coming soon!</i>
        """
        await update.message.reply_text(alerts_text, parse_mode=ParseMode.HTML)
    
    async def report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate comprehensive report of all groups/channels"""
        try:
            user_id = update.effective_user.id
            if str(user_id) != self.config.OWNER_ID:
                await update.message.reply_text("❌ This command is only available for the bot owner.")
                return

            # Show processing message
            processing_msg = await update.message.reply_text("📊 Generating comprehensive report...")
            
            # Initialize reporting system if not already done
            if self.reporting is None:
                self.reporting = ReportingSystem(db, context.bot)
            
            # Generate reports
            quick_report, detailed_report = await self.reporting.generate_owner_report()
            
            # Send in parts (Telegram has message length limits)
            await processing_msg.delete()
            await update.message.reply_text(quick_report, parse_mode=ParseMode.HTML)
            
            if detailed_report:
                await update.message.reply_text(detailed_report, parse_mode=ParseMode.HTML)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error generating report: {str(e)}")
    
    async def group_report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate report for current group"""
        try:
            chat_id = update.effective_chat.id
            
            # Initialize reporting system if not already done
            if self.reporting is None:
                self.reporting = ReportingSystem(db, context.bot)
                
            report = await self.reporting.generate_group_report(chat_id)
            await update.message.reply_text(report, parse_mode=ParseMode.HTML)
        except Exception as e:
            await update.message.reply_text(f"❌ Error generating group report: {str(e)}")
    
    # ===== EXISTING HANDLERS (PRESERVED) =====
    
    async def handle_new_chat_members(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle when bot is added to a new group/channel"""
        print("👥 New chat members event detected")
        new_members = update.message.new_chat_members
        bot_id = context.bot.id
        
        for member in new_members:
            if member.id == bot_id:
                # Bot was added to a group
                chat = update.effective_chat
                print("🎉 Bot added to new community:")
                print("   Chat ID: {}".format(chat.id))
                print("   Chat Title: {}".format(chat.title))
                print("   Chat Type: {}".format(chat.type))
                print("   Added by: {}".format(update.effective_user.id))
                
                db.add_community(chat.id, chat.title, chat.type, update.effective_user.id)
                
                # Request admin permissions
                if chat.type in ['group', 'supergroup']:
                    await self.alert_system.request_admin_permissions(chat.id, bot_id)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Monitor all messages for suspicious activities"""
        message = update.effective_message
        user = update.effective_user
        
        if not message or not user:
            return
        
        # Skip if message is from a bot
        if user.is_bot:
            return
        
        print("💬 Message received from {} in chat {}".format(user.id, message.chat_id))
        
        # Check for suspicious activities
        suspicious_reasons = self.monitor.check_message(message)
        
        if suspicious_reasons:
            user_info = {
                'user_id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'timestamp': message.date.isoformat()
            }
            
            # Log the activity
            db.log_suspicious_activity(
                chat_id=message.chat_id,
                user_id=user.id,
                username=user.username,
                activity_type="suspicious_message",
                description=" | ".join(suspicious_reasons),
                message_content=message.text or message.caption
            )
            
            # Send alert
            await self.alert_system.send_alert(
                chat_id=message.chat_id,
                user_info=user_info,
                reasons=suspicious_reasons,
                message_content=message.text or message.caption
            )
    
    async def setup_commands(self, application):
        """Setup bot commands"""
        print("⚙️ Setting up bot commands...")
        commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("help", "Get help information"),
            BotCommand("stats", "Get group statistics"),
            BotCommand("settings", "Configure bot settings"),
            BotCommand("alerts", "Manage alert preferences"),
            BotCommand("report", "Generate comprehensive report"),
            BotCommand("groupreport", "Get current group status"),
            BotCommand("status", "Check bot status in this chat"),
        ]
        await application.bot.set_my_commands(commands)
        print("✅ Bot commands setup complete")
    
    def run(self):
        """Start the bot"""
        print("\n🚀 Starting bot initialization...")
        
        # Check if BOT_TOKEN is set
        if not self.config.BOT_TOKEN:
            print("❌ CRITICAL: BOT_TOKEN environment variable is not set!")
            print("💡 Get it from @BotFather on Telegram")
            return
        
        if not self.config.OWNER_ID:
            print("❌ CRITICAL: OWNER_ID environment variable is not set!")
            print("💡 Get your user ID from @userinfobot on Telegram")
            return
        
        try:
            print("🔧 Building application...")
            application = Application.builder().token(self.config.BOT_TOKEN).build()
            print("✅ Application built successfully")
            
            # Add handlers
            print("🔧 Adding command handlers...")
            application.add_handler(CommandHandler("start", self.start))
            application.add_handler(CommandHandler("help", self.help_command))
            application.add_handler(CommandHandler("stats", self.stats_command))
            application.add_handler(CommandHandler("settings", self.settings_command))
            application.add_handler(CommandHandler("alerts", self.alerts_command))
            application.add_handler(CommandHandler("report", self.report_command))
            application.add_handler(CommandHandler("groupreport", self.group_report_command))
            application.add_handler(CommandHandler("status", self.start))
            application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, self.handle_new_chat_members))
            application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, self.handle_message))
            print("✅ Handlers added successfully")
            
            # Setup commands
            application.post_init = self.setup_commands
            
            print("\n" + "="*50)
            print("✅ BOT INITIALIZATION COMPLETE")
            print("🤖 Bot is starting...")
            print("📱 Send /start to your bot to test it")
            print("="*50 + "\n")
            
            # Start the bot
            print("🌐 Starting polling...")
            application.run_polling(allowed_updates=Update.ALL_TYPES)
                
        except Exception as e:
            print("❌ CRITICAL: Failed to start bot: {}".format(e))
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    try:
        bot = ProtectionBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print("❌ Unexpected error: {}".format(e))
        import traceback
        traceback.print_exc()
