import os
import logging
from telegram import Update, BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ContextTypes, CallbackContext
)
from telegram.constants import ParseMode

from database import Session, Community, AlertSettings
from monitoring import ActivityMonitor
from alert_system import AlertSystem
import config

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ProtectionBot:
    def __init__(self):
        self.config = config.Config()
        self.monitor = ActivityMonitor()
        self.alert_system = AlertSystem(self.config.BOT_TOKEN)
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send welcome message when the bot is started"""
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
        await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML)
    
    async def handle_new_chat_members(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle when bot is added to a new group/channel"""
        new_members = update.message.new_chat_members
        bot_id = context.bot.id
        
        for member in new_members:
            if member.id == bot_id:
                # Bot was added to a group
                chat = update.effective_chat
                await self._register_community(chat, update.effective_user.id)
                
                # Request admin permissions
                if chat.type in ['group', 'supergroup']:
                    await self.alert_system.request_admin_permissions(chat.id, bot_id)
    
    async def _register_community(self, chat, owner_id):
        """Register a new community in database"""
        session = Session()
        try:
            community = Community(
                chat_id=str(chat.id),
                chat_title=chat.title,
                chat_type=chat.type,
                owner_id=str(owner_id)
            )
            session.add(community)
            session.commit()
            logger.info(f"Registered new community: {chat.title}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error registering community: {e}")
        finally:
            session.close()
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Monitor all messages for suspicious activities"""
        message = update.effective_message
        user = update.effective_user
        
        if not message or not user:
            return
        
        # Skip if message is from a bot
        if user.is_bot:
            return
        
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
            self.monitor.log_activity(
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
    
    async def check_admin_status(self, context: CallbackContext):
        """Periodically check if bot has admin permissions"""
        session = Session()
        try:
            communities = session.query(Community).all()
            
            for community in communities:
                try:
                    chat = await context.bot.get_chat(community.chat_id)
                    bot_member = await chat.get_member(context.bot.id)
                    
                    # Check if bot is admin with necessary permissions
                    if bot_member.status in ['administrator', 'creator']:
                        if bot_member.can_delete_messages and bot_member.can_restrict_members:
                            community.has_full_permissions = True
                        else:
                            community.has_full_permissions = False
                    else:
                        community.has_full_permissions = False
                    
                    community.is_bot_admin = bot_member.status in ['administrator', 'creator']
                    session.commit()
                    
                except Exception as e:
                    logger.error(f"Error checking admin status for {community.chat_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in admin status check: {e}")
        finally:
            session.close()
    
    async def setup_commands(self, application: Application):
        """Setup bot commands"""
        commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("help", "Get help information"),
            BotCommand("status", "Check bot status in this chat"),
        ]
        await application.bot.set_my_commands(commands)
    
    def run(self):
        """Start the bot"""
        application = Application.builder().token(self.config.BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.start))
        application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, self.handle_new_chat_members))
        application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, self.handle_message))
        
        # Add job queue for periodic tasks
        job_queue = application.job_queue
        if job_queue:
            job_queue.run_repeating(self.check_admin_status, interval=300, first=10)  # Every 5 minutes
        
        # Setup commands
        application.post_init = self.setup_commands
        
        # Start the bot
        if os.getenv('RENDER'):
            # On Render, use webhook (optional for background worker)
            port = int(os.getenv('PORT', 8443))
            application.run_webhook(
                listen="0.0.0.0",
                port=port,
                url_path=self.config.BOT_TOKEN,
                webhook_url=f"https://your-app-name.onrender.com/{self.config.BOT_TOKEN}"
            )
        else:
            # Local development - use polling
            application.run_polling()

if __name__ == '__main__':
    bot = ProtectionBot()
    bot.run()
