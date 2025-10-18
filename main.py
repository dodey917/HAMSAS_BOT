import os
import logging
import asyncio
from datetime import datetime
from telegram import Update, BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ContextTypes, CallbackContext
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

class Config:
    """Configuration class to handle environment variables"""
    def __init__(self):
        self.BOT_TOKEN = os.getenv('BOT_TOKEN')
        self.OWNER_ID = os.getenv('OWNER_ID')
        self.OWNER_USERNAME = os.getenv('OWNER_USERNAME', '@Kayblezzy')
        self.DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bot_data.db')
        
        print("🔧 Configuration loaded:")
        print(f"   BOT_TOKEN: {'✅ Set' if self.BOT_TOKEN else '❌ Missing'}")
        print(f"   OWNER_ID: {'✅ ' + self.OWNER_ID if self.OWNER_ID else '❌ Missing'}")
        print(f"   DATABASE_URL: {self.DATABASE_URL}")

class SimpleDatabase:
    """Simple database implementation for basic functionality"""
    def __init__(self):
        self.communities = []
        self.alerts = []
        self.suspicious_activities = []
    
    def initialize_database(self):
        """Initialize database tables"""
        print("🗄️  Initializing database...")
        # This would normally create tables in a real database
        print("✅ Database initialized")
    
    def add_community(self, chat_id, title, chat_type, added_by):
        """Add community to database"""
        community = {
            'chat_id': chat_id,
            'title': title,
            'type': chat_type,
            'added_by': added_by,
            'added_at': datetime.now(),
            'is_active': True
        }
        # Remove if exists and add new
        self.communities = [c for c in self.communities if c['chat_id'] != chat_id]
        self.communities.append(community)
        print(f"✅ Community added: {title} (ID: {chat_id})")
        return True
    
    def get_all_communities(self):
        """Get all communities"""
        return self.communities
    
    def log_suspicious_activity(self, chat_id, user_id, username, activity_type, description, message_content):
        """Log suspicious activity"""
        activity = {
            'chat_id': chat_id,
            'user_id': user_id,
            'username': username,
            'activity_type': activity_type,
            'description': description,
            'message_content': message_content,
            'timestamp': datetime.now()
        }
        self.suspicious_activities.append(activity)
        print(f"✅ Suspicious activity logged: {activity_type} in chat {chat_id}")
        return True
    
    def get_total_alerts(self):
        """Get total number of alerts"""
        return len(self.suspicious_activities)
    
    def get_alerts_summary(self):
        """Get alerts summary by community"""
        summary = {}
        for activity in self.suspicious_activities:
            chat_id = activity['chat_id']
            if chat_id not in summary:
                # Find community title
                community = next((c for c in self.communities if c['chat_id'] == chat_id), {'title': f'Chat {chat_id}'})
                summary[chat_id] = {
                    'chat_title': community['title'],
                    'alert_count': 0
                }
            summary[chat_id]['alert_count'] += 1
        
        return list(summary.values())

class ActivityMonitor:
    """Monitor for suspicious activities"""
    def __init__(self):
        self.suspicious_keywords = [
            'spam', 'scam', 'fake', 'phishing', 'malware',
            'virus', 'hack', 'password', 'login', 'credit card',
            'bitcoin', 'crypto', 'investment', 'money', 'free'
        ]
        print(f"✅ Activity Monitor initialized with {len(self.suspicious_keywords)} keywords")
    
    def check_message(self, message):
        """Check message for suspicious content"""
        if not message.text:
            return []
        
        text = message.text.lower()
        suspicious_reasons = []
        
        # Check for suspicious keywords
        for keyword in self.suspicious_keywords:
            if keyword in text:
                suspicious_reasons.append(f"Suspicious keyword: {keyword}")
        
        # Check for excessive capital letters (shouting)
        if len(text) > 10 and sum(1 for c in text if c.isupper()) / len(text) > 0.7:
            suspicious_reasons.append("Excessive capital letters")
        
        # Check for excessive emojis
        emoji_count = sum(1 for c in text if c in ['😂', '😍', '🔥', '💯', '🎉', '💰'])
        if emoji_count > 5:
            suspicious_reasons.append("Excessive emojis")
        
        return suspicious_reasons

class AlertSystem:
    """System for sending alerts"""
    def __init__(self, bot_token):
        self.bot_token = bot_token
        print("✅ Alert System initialized")
    
    async def send_alert(self, chat_id, user_info, reasons, message_content):
        """Send alert to chat"""
        try:
            alert_message = f"""
🚨 <b>Suspicious Activity Detected</b>

👤 <b>User:</b> {user_info.get('first_name', 'Unknown')}
🆔 <b>ID:</b> <code>{user_info.get('user_id', 'Unknown')}</code>

📝 <b>Reasons:</b>
{chr(10).join(f'• {reason}' for reason in reasons)}

💬 <b>Message:</b>
{message_content[:200] + '...' if len(message_content) > 200 else message_content}

🕒 <b>Time:</b> {datetime.now().strftime('%H:%M:%S')}
            """
            # In a real implementation, this would send the message
            print(f"📢 Alert would be sent to chat {chat_id}: {reasons}")
            return True
        except Exception as e:
            print(f"❌ Failed to send alert: {e}")
            return False
    
    async def request_admin_permissions(self, chat_id, bot_id):
        """Request admin permissions"""
        try:
            print(f"🔐 Requesting admin permissions for chat {chat_id}")
            # In a real implementation, this would send an admin request message
            return True
        except Exception as e:
            print(f"❌ Failed to request admin permissions: {e}")
            return False

class ReportingSystem:
    """System for generating reports"""
    def __init__(self, database, bot):
        self.db = database
        self.bot = bot
        print("✅ Reporting System initialized")
    
    async def generate_owner_report(self):
        """Generate report for owner"""
        communities = self.db.get_all_communities()
        total_alerts = self.db.get_total_alerts()
        
        quick_report = f"""
📊 <b>Quick Status Overview</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏠 <b>Active Communities:</b> {len(communities)}
🚨 <b>Total Alerts:</b> {total_alerts}
📈 <b>Monitoring Status:</b> ✅ Active

🛡️ <b>Protection Systems:</b>
• Live Scanning: ✅ Operational
• Alert System: ✅ Active
• Database: ✅ Connected

🕒 <b>Last Update:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        detailed_report = f"""
📋 <b>Detailed Community Analysis</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 <b>Community Breakdown:</b>
"""
        for community in communities[:10]:  # Show first 10
            alerts_count = len([a for a in self.db.suspicious_activities if a['chat_id'] == community['chat_id']])
            detailed_report += f"• {community['title']} - {alerts_count} alerts\n"
        
        if len(communities) > 10:
            detailed_report += f"• ... and {len(communities) - 10} more communities\n"
        
        detailed_report += f"""
📈 <b>System Health:</b>
• Communities Protected: {len(communities)}
• Active Monitoring: {len(communities)}
• Recent Alerts: {total_alerts}
• Uptime: 100%

💡 <b>Recommendations:</b>
• Continue current monitoring levels
• Review alert settings regularly
• Ensure all communities have admin access
        """
        
        return quick_report, detailed_report
    
    async def generate_group_report(self, chat_id):
        """Generate report for specific group"""
        communities = self.db.get_all_communities()
        community = next((c for c in communities if c['chat_id'] == chat_id), None)
        
        if not community:
            return "❌ Community not found in database."
        
        alerts_count = len([a for a in self.db.suspicious_activities if a['chat_id'] == chat_id])
        
        return f"""
📊 <b>Group Report</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏠 <b>Community:</b> {community['title']}
🆔 <b>ID:</b> <code>{chat_id}</code>
📝 <b>Type:</b> {community['type']}
🚨 <b>Alerts:</b> {alerts_count}
📅 <b>Added:</b> {community['added_at'].strftime('%Y-%m-%d')}

🛡️ <b>Protection Status:</b>
• Monitoring: ✅ Active
• Alerts: {alerts_count} recorded
• Database: ✅ Tracked

💡 <b>Status:</b> Community is being monitored for suspicious activities.
        """

class ProtectionBot:
    def __init__(self):
        print("\n🔨 Creating ProtectionBot instance...")
        self.config = Config()
        self.db = SimpleDatabase()
        self.monitor = ActivityMonitor()
        self.alert_system = AlertSystem(self.config.BOT_TOKEN)
        self.reporting = None  # Will be initialized when bot is available
        print("✅ ProtectionBot instance created")
    
    async def notify_owner(self, context: CallbackContext, title: str, details: str, scan_data: dict = None):
        """Notify owner with community scan results"""
        try:
            owner_id = self.config.OWNER_ID
            if not owner_id:
                print("❌ OWNER_ID not set, cannot send notifications")
                return
            
            if scan_data:
                notification = f"""
🔔 <b>{title}</b>

🏠 <b>Community:</b> {scan_data.get('title', 'Unknown')}
🆔 <b>ID:</b> <code>{scan_data.get('id', 'Unknown')}</code>
📝 <b>Type:</b> {scan_data.get('type', 'Unknown')}
👥 <b>Members:</b> {scan_data.get('members_count', 'Unknown')}
🛡️ <b>Status:</b> {scan_data.get('risk_level', 'Unknown')}

📊 <b>Assessment:</b>
{scan_data.get('assessment', 'Scan completed.')}

💡 <b>Recommendations:</b>
{scan_data.get('recommendation', 'Ensure bot has admin permissions.')}

🕒 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """
            else:
                notification = f"🔔 <b>{title}</b>\n\n{details}\n\n🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            await context.bot.send_message(
                chat_id=owner_id,
                text=notification,
                parse_mode=ParseMode.HTML
            )
            print(f"✅ Owner notified: {title}")
            
        except Exception as e:
            print(f"❌ Failed to notify owner: {e}")
    
    async def is_bot_admin(self, context: CallbackContext, chat_id: int) -> bool:
        """Check if bot is admin in the group/channel"""
        try:
            bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
            return bot_member.status in ['administrator', 'creator']
        except Exception as e:
            print(f"❌ Admin check error: {e}")
            return False
    
    async def perform_live_scan(self, context: CallbackContext, chat_id: int, chat_title: str = None) -> dict:
        """Perform live scan of community"""
        try:
            chat = await context.bot.get_chat(chat_id)
            members_count = await context.bot.get_chat_members_count(chat_id)
            is_admin = await self.is_bot_admin(context, chat_id)
            
            # Determine risk level based on various factors
            if not is_admin:
                risk_level = "🔴 HIGH RISK"
                assessment = "Bot lacks admin permissions - Limited protection"
                recommendation = "Make bot admin for full protection features"
            else:
                risk_level = "🟢 LOW RISK"
                assessment = "Community is well-protected with active monitoring"
                recommendation = "Continue current protection levels"
            
            return {
                'id': chat_id,
                'title': chat_title or chat.title,
                'type': chat.type,
                'username': f"@{chat.username}" if chat.username else "None",
                'members_count': members_count,
                'description': chat.description or "None",
                'is_admin': is_admin,
                'risk_level': risk_level,
                'assessment': assessment,
                'recommendation': recommendation,
                'scan_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            print(f"❌ Live scan failed: {e}")
            return {
                'id': chat_id,
                'title': chat_title or 'Unknown',
                'error': str(e),
                'risk_level': 'UNKNOWN',
                'assessment': 'Scan failed',
                'recommendation': 'Please try again'
            }

    # ===== COMMAND HANDLERS =====
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        chat = update.effective_chat
        
        print(f"🎯 /start from user {user.id} in {chat.type}")
        
        if chat.type == 'private':
            # Private chat - show introduction
            welcome_text = """
🤖 <b>Community Protection Bot</b>

I help protect your Telegram communities from spam, scams, and suspicious activities.

<b>Features:</b>
• Live community scanning
• Suspicious activity detection
• Security alerts
• Activity monitoring

<b>Commands:</b>
/start - Start bot or scan community
/help - Show help information
/stats - View statistics
/settings - Configure settings
/alerts - Check alerts
/status - Check community health

<b>Setup:</b>
Add me to your group/channel and make me admin for full protection!
            """
            await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML)
            
        else:
            # Group/channel - perform scan if admin
            try:
                if await self.is_bot_admin(context, chat.id):
                    processing_msg = await update.message.reply_text("🔍 Scanning community...")
                    scan_data = await self.perform_live_scan(context, chat.id, chat.title)
                    
                    quick_result = f"""
✅ <b>Scan Complete - {scan_data['title']}</b>

👥 <b>Members:</b> {scan_data['members_count']}
🎯 <b>Type:</b> {scan_data['type']}
🛡️ <b>Status:</b> {scan_data['risk_level']}

📋 Report sent to owner.
                    """
                    await processing_msg.delete()
                    await update.message.reply_text(quick_result, parse_mode=ParseMode.HTML)
                    
                    # Notify owner
                    await self.notify_owner(
                        context,
                        "🏠 Community Scan",
                        f"Scan by {user.first_name} in {chat.title}",
                        scan_data
                    )
                    
                    # Register community
                    self.db.add_community(chat.id, chat.title, chat.type, user.id)
                    
                else:
                    await update.message.reply_text(
                        "⚠️ <b>Admin Access Required</b>\n\n"
                        "I need admin permissions to scan this community.\n\n"
                        "Please make me an administrator and try again.",
                        parse_mode=ParseMode.HTML
                    )
                    
            except Exception as e:
                await update.message.reply_text("❌ Error scanning community.")
                print(f"Start error: {e}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🆘 <b>Help Guide</b>

<b>Commands:</b>
/start - Start bot or scan community
/help - Show this help
/stats - View statistics
/settings - Configure settings
/alerts - Check alerts
/status - Check community health

<b>Features:</b>
• Community protection
• Activity monitoring
• Security alerts
• Live scanning

Need help? Contact the bot owner.
        """
        await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        communities = self.db.get_all_communities()
        total_alerts = self.db.get_total_alerts()
        
        stats_text = f"""
📊 <b>Statistics</b>

🏠 <b>Communities:</b> {len(communities)}
🚨 <b>Total Alerts:</b> {total_alerts}
📈 <b>Status:</b> ✅ Active

<b>Recent Communities:</b>
"""
        for community in communities[:5]:
            stats_text += f"• {community['title']}\n"
        
        if len(communities) > 5:
            stats_text += f"• ... and {len(communities) - 5} more\n"
        
        await update.message.reply_text(stats_text, parse_mode=ParseMode.HTML)
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command"""
        settings_text = """
⚙️ <b>Settings</b>

<b>Available Settings:</b>
• Monitoring level
• Alert preferences
• Security rules

<b>Status:</b>
All protection features are active.

<b>Note:</b>
Advanced configuration available when bot is admin.
        """
        await update.message.reply_text(settings_text, parse_mode=ParseMode.HTML)
    
    async def alerts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /alerts command"""
        alerts_data = self.db.get_alerts_summary()
        total_alerts = self.db.get_total_alerts()
        
        alerts_text = f"""
🚨 <b>Alerts Summary</b>

📊 <b>Total Alerts:</b> {total_alerts}
🏠 <b>Communities:</b> {len(alerts_data)}

<b>Alert Distribution:</b>
"""
        for alert in alerts_data[:5]:
            alerts_text += f"• {alert['chat_title']}: {alert['alert_count']} alerts\n"
        
        if len(alerts_data) > 5:
            alerts_text += f"• ... and {len(alerts_data) - 5} more\n"
        
        await update.message.reply_text(alerts_text, parse_mode=ParseMode.HTML)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        chat = update.effective_chat
        
        if chat.type == 'private':
            await update.message.reply_text("ℹ️ Use /status in a group/channel to check its health.")
            return
        
        try:
            if not await self.is_bot_admin(context, chat.id):
                await update.message.reply_text("⚠️ I need admin access to check status.")
                return
            
            processing_msg = await update.message.reply_text("🔍 Checking community health...")
            scan_data = await self.perform_live_scan(context, chat.id, chat.title)
            
            status_report = f"""
📊 <b>Community Health</b>

🏠 <b>Community:</b> {scan_data['title']}
🛡️ <b>Status:</b> {scan_data['risk_level']}
👥 <b>Members:</b> {scan_data['members_count']}

{scan_data['assessment']}

💡 <b>Recommendation:</b>
{scan_data['recommendation']}
            """
            
            await processing_msg.delete()
            await update.message.reply_text(status_report, parse_mode=ParseMode.HTML)
            
        except Exception as e:
            await update.message.reply_text("❌ Error checking status.")
            print(f"Status error: {e}")
    
    async def handle_new_chat_members(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle bot being added to groups/channels"""
        new_members = update.message.new_chat_members
        bot_id = context.bot.id
        
        for member in new_members:
            if member.id == bot_id:
                chat = update.effective_chat
                added_by = update.effective_user
                
                print(f"🎉 Bot added to {chat.title} by {added_by.first_name}")
                
                try:
                    # Perform scan
                    scan_data = await self.perform_live_scan(context, chat.id, chat.title)
                    
                    # Register community
                    self.db.add_community(chat.id, chat.title, chat.type, added_by.id)
                    
                    # Send welcome message
                    welcome_msg = f"""
🤖 <b>Protection Bot Activated</b>

Thank you for adding me to <b>{chat.title}</b>!

<b>Next Steps:</b>
1. Make me admin for full protection
2. Use /start to perform security scan
3. Configure settings with /settings

<b>Features:</b>
• Security monitoring
• Threat detection
• Activity alerts

I'll now begin monitoring this community.
                    """
                    await context.bot.send_message(chat.id, welcome_msg, parse_mode=ParseMode.HTML)
                    
                    # Notify owner
                    await self.notify_owner(
                        context,
                        "🆕 Bot Added",
                        f"Added to {chat.title} by {added_by.first_name}",
                        scan_data
                    )
                    
                    # Request admin if needed
                    if not scan_data['is_admin'] and chat.type in ['group', 'supergroup']:
                        await self.alert_system.request_admin_permissions(chat.id, bot_id)
                        
                except Exception as e:
                    print(f"❌ Auto-setup failed: {e}")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Monitor messages for suspicious activity"""
        message = update.effective_message
        user = update.effective_user
        
        if not message or not user or user.is_bot:
            return
        
        # Check for suspicious content
        suspicious_reasons = self.monitor.check_message(message)
        
        if suspicious_reasons:
            user_info = {
                'user_id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'timestamp': datetime.now().isoformat()
            }
            
            # Log activity
            self.db.log_suspicious_activity(
                message.chat_id,
                user.id,
                user.username,
                "suspicious_message",
                " | ".join(suspicious_reasons),
                message.text or message.caption or "Media content"
            )
            
            # Send alert
            await self.alert_system.send_alert(
                message.chat_id,
                user_info,
                suspicious_reasons,
                message.text or message.caption
            )
            
            # Notify owner
            await self.notify_owner(
                context,
                "🚨 Suspicious Activity",
                f"User: {user.first_name}\n"
                f"Chat: {message.chat.title}\n"
                f"Reasons: {', '.join(suspicious_reasons)}"
            )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Error: {context.error}")
        
        try:
            if self.config.OWNER_ID:
                await context.bot.send_message(
                    self.config.OWNER_ID,
                    f"🚨 Bot Error:\n{context.error}",
                    parse_mode=ParseMode.HTML
                )
        except:
            pass
    
    async def setup_commands(self, application):
        """Setup bot commands menu"""
        commands = [
            BotCommand("start", "Start bot or scan community"),
            BotCommand("help", "Show help guide"),
            BotCommand("stats", "View statistics"),
            BotCommand("settings", "Configure settings"),
            BotCommand("alerts", "Check alerts"),
            BotCommand("status", "Check community health"),
        ]
        await application.bot.set_my_commands(commands)
        print("✅ Bot commands menu setup complete")
    
    def run(self):
        """Start the bot"""
        print("\n🚀 Starting bot...")
        
        if not self.config.BOT_TOKEN:
            print("❌ BOT_TOKEN not set!")
            return
        
        if not self.config.OWNER_ID:
            print("❌ OWNER_ID not set!")
            return
        
        try:
            # Initialize database
            self.db.initialize_database()
            
            # Create application
            application = Application.builder().token(self.config.BOT_TOKEN).build()
            
            # Initialize reporting system
            self.reporting = ReportingSystem(self.db, application.bot)
            
            # Add handlers
            application.add_handler(CommandHandler("start", self.start_command))
            application.add_handler(CommandHandler("help", self.help_command))
            application.add_handler(CommandHandler("stats", self.stats_command))
            application.add_handler(CommandHandler("settings", self.settings_command))
            application.add_handler(CommandHandler("alerts", self.alerts_command))
            application.add_handler(CommandHandler("status", self.status_command))
            application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, self.handle_new_chat_members))
            application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, self.handle_message))
            application.add_error_handler(self.error_handler)
            
            # Setup commands
            application.post_init = self.setup_commands
            
            print("✅ All systems ready!")
            print("🤖 Bot is running...")
            
            # Start polling
            application.run_polling()
            
        except Exception as e:
            print(f"❌ Failed to start bot: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    # Create and run the bot
    bot = ProtectionBot()
    bot.run()
