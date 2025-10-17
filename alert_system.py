from telegram import Bot
from database import db
import config

print("🚨 Initializing Alert System...")

class AlertSystem:
    def __init__(self, bot_token):
        self.config = config.Config()
        self.bot_token = bot_token
        
        if not bot_token:
            print("❌ AlertSystem: No bot token provided!")
            self.bot = None
            return
            
        try:
            self.bot = Bot(bot_token)
            print("✅ Alert System initialized with bot token")
            # Don't test the bot here - it causes async issues
            # We'll test it when we actually need to send messages
        except Exception as e:
            print("❌ AlertSystem: Failed to initialize bot: {}".format(e))
            self.bot = None
            
        self.cooldown_users = set()
        print("✅ Alert System ready")
    
    async def send_alert(self, chat_id, user_info, reasons, message_content=""):
        """Send alert to community owner"""
        if not self.bot:
            print("❌ Cannot send alert: Bot not initialized")
            return False
            
        print("📤 Sending alert for chat: {}".format(chat_id))
        
        try:
            # Get community owner
            owner_id = db.get_community_owner(chat_id)
            if not owner_id:
                print("❌ No owner found for chat {}".format(chat_id))
                return False
            
            print("   Target owner: {}".format(owner_id))
            
            # Check cooldown
            cooldown_key = f"{chat_id}_{user_info['user_id']}"
            if cooldown_key in self.cooldown_users:
                print("   ⏸️  Alert skipped (cooldown)")
                return True
            
            # Prepare alert message
            alert_message = self._format_alert_message(
                "Protected Community",
                user_info,
                reasons,
                message_content
            )
            
            # Send alert to owner
            try:
                print("   ✉️  Sending message to owner...")
                await self.bot.send_message(
                    chat_id=owner_id,
                    text=alert_message,
                    parse_mode='HTML'
                )
                
                # Add to cooldown
                self.cooldown_users.add(cooldown_key)
                print("   ✅ Alert sent successfully to owner {}".format(owner_id))
                
            except Exception as e:
                print("❌ Failed to send alert to owner: {}".format(e))
                return False
            
            return True
            
        except Exception as e:
            print("❌ Error in alert system: {}".format(e))
            return False
    
    def _format_alert_message(self, chat_title, user_info, reasons, message_content):
        """Format the alert message"""
        message = f"🚨 <b>Security Alert</b> 🚨\n\n"
        message += f"<b>Community:</b> {chat_title}\n"
        message += f"<b>User:</b> {user_info.get('username', 'N/A')} (ID: {user_info['user_id']})\n"
        message += f"<b>First Name:</b> {user_info.get('first_name', 'N/A')}\n"
        message += f"<b>Last Name:</b> {user_info.get('last_name', 'N/A')}\n\n"
        
        message += "<b>Reasons for Alert:</b>\n"
        for i, reason in enumerate(reasons, 1):
            message += f"{i}. {reason}\n"
        
        if message_content:
            message += f"\n<b>Message Content:</b>\n<code>{message_content[:500]}</code>"
        
        message += f"\n\n⏰ <i>Alert generated at: {user_info.get('timestamp', 'N/A')}</i>"
        
        return message
    
    async def request_admin_permissions(self, chat_id, bot_id):
        """Request admin permissions for the bot"""
        if not self.bot:
            print("❌ Cannot request permissions: Bot not initialized")
            return
            
        try:
            print("🛡️  Requesting admin permissions in chat: {}".format(chat_id))
            message = (
                "🔒 <b>Protection Bot Setup Required</b>\n\n"
                "To fully protect this community, I need administrator permissions with:\n"
                "• Delete messages permission\n"
                "• Ban users permission\n"
                "• Pin messages permission\n"
                "• Invite users permission\n"
                "• Manage chat permission\n\n"
                "Please promote me to admin with these permissions to enable full protection."
            )
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='HTML'
            )
            print("✅ Admin permission request sent")
        except Exception as e:
            print("❌ Error requesting admin permissions: {}".format(e))

print("✅ Alert System module loaded successfully!\n")
