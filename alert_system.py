from telegram import Bot
from database import Session, Community, AlertSettings
import config

class AlertSystem:
    def __init__(self, bot_token):
        self.bot = Bot(bot_token)
        self.cooldown_users = set()
    
    async def send_alert(self, chat_id, user_info, reasons, message_content=""):
        """Send alert to community owner"""
        session = Session()
        try:
            # Get community info
            community = session.query(Community).filter_by(chat_id=str(chat_id)).first()
            if not community or not community.owner_id:
                return False
            
            # Get alert settings
            alert_settings = session.query(AlertSettings).filter_by(chat_id=str(chat_id)).first()
            if not alert_settings:
                alert_settings = AlertSettings(chat_id=str(chat_id))
                session.add(alert_settings)
                session.commit()
            
            # Check cooldown
            cooldown_key = f"{chat_id}_{user_info['user_id']}"
            if cooldown_key in self.cooldown_users:
                return True
            
            # Prepare alert message
            alert_message = self._format_alert_message(
                community.chat_title,
                user_info,
                reasons,
                message_content
            )
            
            # Send alert to owner
            if alert_settings.alert_owner:
                try:
                    await self.bot.send_message(
                        chat_id=community.owner_id,
                        text=alert_message,
                        parse_mode='HTML'
                    )
                    
                    # Add to cooldown
                    self.cooldown_users.add(cooldown_key)
                    
                except Exception as e:
                    print(f"Failed to send alert to owner: {e}")
            
            return True
            
        except Exception as e:
            print(f"Error in alert system: {e}")
            return False
        finally:
            session.close()
    
    def _format_alert_message(self, chat_title, user_info, reasons, message_content):
        """Format the alert message"""
        message = f"🚨 <b>Security Alert</b> 🚨\n\n"
        message += f"<b>Community:</b> {chat_title or 'Unknown'}\n"
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
        try:
            # This would typically be sent to the group admin
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
        except Exception as e:
            print(f"Error requesting admin permissions: {e}")
