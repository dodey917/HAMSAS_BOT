import asyncio
import logging
from datetime import datetime, timedelta
from database import Database

class AlertSystem:
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.logger = logging.getLogger(__name__)
    
    async def request_admin_permissions(self, chat_id, bot_id):
        """Request admin permissions for the bot in a group"""
        try:
            # Create a custom keyboard with admin request button
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
            keyboard = [
                [InlineKeyboardButton("Grant Admin Permissions", 
                                    url=f"t.me/{bot_id}?startgroup=admin&admin=1")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = (
                "🔐 **Admin Permissions Required**\n\n"
                "To properly monitor this group and protect against threats, "
                "I need the following permissions:\n\n"
                "• ✅ Delete messages\n"
                "• ✅ Ban users\n" 
                "• ✅ Invite users via link\n"
                "• ✅ Pin messages\n"
                "• ✅ Manage video chats\n\n"
                "Please grant these permissions to ensure the security of this group."
            )
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Error requesting admin permissions: {e}")
            return False
    
    async def send_alert(self, chat_id, alert_type, details, severity="medium"):
        """Send security alerts to the group"""
        try:
            # Get alert settings for this community
            alert_settings = self.db.get_alert_settings(chat_id)
            
            if not alert_settings:
                # Create default settings if none exist
                alert_settings = {
                    'suspicious_login': True,
                    'mass_joining': True,
                    'spam_detected': True,
                    'admin_actions': True
                }
            
            # Check if this alert type is enabled
            if not alert_settings.get(alert_type, True):
                return False
            
            # Format alert message based on type and severity
            emoji = "🔴" if severity == "high" else "🟡" if severity == "medium" else "🔵"
            
            alert_messages = {
                "suspicious_login": f"{emoji} **Suspicious Login Detected**\n\n{details}",
                "mass_joining": f"{emoji} **Mass Joining Activity**\n\n{details}",
                "spam_detected": f"{emoji} **Spam Content Detected**\n\n{details}",
                "admin_actions": f"{emoji} **Admin Action Required**\n\n{details}",
                "threat_detected": f"{emoji} **Security Threat Detected**\n\n{details}"
            }
            
            message = alert_messages.get(alert_type, f"{emoji} **Security Alert**\n\n{details}")
            
            # Add timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message += f"\n\n🕒 _Detected at {timestamp}_"
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown'
            )
            
            # Log the alert in database
            self.db.log_suspicious_activity(chat_id, alert_type, details, severity)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending alert: {e}")
            return False
    
    async def alert_admins(self, chat_id, message, mention_admins=False):
        """Alert all admins in the group"""
        try:
            # Get chat administrators
            admins = await self.bot.get_chat_administrators(chat_id)
            
            if mention_admins:
                # Mention admins in the message
                admin_mentions = []
                for admin in admins:
                    if not admin.user.is_bot and admin.user.username:
                        admin_mentions.append(f"@{admin.user.username}")
                
                if admin_mentions:
                    message += f"\n\n👮 **Admins:** {' '.join(admin_mentions)}"
            
            # Send alert to the group
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown'
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error alerting admins: {e}")
            return False
    
    async def update_alert_settings(self, chat_id, settings):
        """Update alert settings for a community"""
        try:
            return self.db.update_alert_settings(chat_id, settings)
        except Exception as e:
            self.logger.error(f"Error updating alert settings: {e}")
            return False
    
    async def get_alert_stats(self, chat_id, days=7):
        """Get alert statistics for a community"""
        try:
            since_date = datetime.now() - timedelta(days=days)
            activities = self.db.get_suspicious_activities_since(chat_id, since_date)
            
            stats = {
                'total': len(activities),
                'high_severity': len([a for a in activities if a.get('severity') == 'high']),
                'medium_severity': len([a for a in activities if a.get('severity') == 'medium']),
                'low_severity': len([a for a in activities if a.get('severity') == 'low']),
                'by_type': {}
            }
            
            # Count by type
            for activity in activities:
                alert_type = activity.get('activity_type', 'unknown')
                stats['by_type'][alert_type] = stats['by_type'].get(alert_type, 0) + 1
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting alert stats: {e}")
            return {}
    
    async def send_daily_report(self, chat_id):
        """Send daily security report"""
        try:
            stats = await self.get_alert_stats(chat_id, days=1)
            
            if stats['total'] == 0:
                message = (
                    "📊 **Daily Security Report**\n\n"
                    "✅ No security issues detected today!\n\n"
                    "Your community remains secure and protected."
                )
            else:
                message = (
                    "📊 **Daily Security Report**\n\n"
                    f"🔍 **Activities Detected:** {stats['total']}\n"
                    f"🔴 High Severity: {stats['high_severity']}\n"
                    f"🟡 Medium Severity: {stats['medium_severity']}\n"
                    f"🔵 Low Severity: {stats['low_severity']}\n\n"
                )
                
                # Add breakdown by type
                if stats['by_type']:
                    message += "**Breakdown by Type:**\n"
                    for alert_type, count in stats['by_type'].items():
                        message += f"• {alert_type.replace('_', ' ').title()}: {count}\n"
            
            message += f"\n🕒 _Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M')}_"
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown'
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending daily report: {e}")
            return False

# Utility functions for common alert patterns
async def create_spam_alert(alert_system, chat_id, user_info, message_content, pattern_detected):
    """Create and send a spam detection alert"""
    details = (
        f"**User:** {user_info}\n"
        f"**Pattern:** {pattern_detected}\n"
        f"**Content:** {message_content[:200]}..."
    )
    
    return await alert_system.send_alert(
        chat_id=chat_id,
        alert_type="spam_detected",
        details=details,
        severity="high"
    )

async def create_mass_join_alert(alert_system, chat_id, users_info, time_frame):
    """Create and send a mass joining alert"""
    details = (
        f"**Users Joined:** {len(users_info)}\n"
        f"**Time Frame:** {time_frame} minutes\n"
        f"**First 5 Users:** {', '.join(users_info[:5])}"
    )
    
    return await alert_system.send_alert(
        chat_id=chat_id,
        alert_type="mass_joining",
        details=details,
        severity="medium"
    )

async def create_suspicious_login_alert(alert_system, chat_id, user_info, location, device):
    """Create and send a suspicious login alert"""
    details = (
        f"**User:** {user_info}\n"
        f"**Location:** {location}\n"
        f"**Device:** {device}\n"
        f"**Action:** Immediate verification recommended"
    )
    
    return await alert_system.send_alert(
        chat_id=chat_id,
        alert_type="suspicious_login",
        details=details,
        severity="high"
    )
