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
        print("✅ ProtectionBot instance created")
        
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

Developed with ❤️ for Telegram community safety.
        """
        try:
            await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML)
            print("✅ Welcome message sent successfully")
        except Exception as e:
            print("❌ Failed to send welcome message: {}".format(e))
    
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
            application.add_handler(CommandHandler("help", self.start))
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
