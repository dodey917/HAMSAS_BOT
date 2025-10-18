import os
import logging
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

# Import our modules after logging is set up
try:
    from database import db
    from monitoring import ActivityMonitor
    from alert_system import AlertSystem
    from reporting import ReportingSystem
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
        self.reporting = None
        print("✅ ProtectionBot instance created")
    
    async def notify_owner(self, context: CallbackContext, title: str, details: str, scan_data: dict = None):
        """Notify owner with community scan results and command activities"""
        try:
            owner_id = self.config.OWNER_ID
            if not owner_id:
                print("❌ OWNER_ID not set, cannot send notifications")
                return
            
            if scan_data:
                # Comprehensive scan report
                notification = f"""
🔔 <b>{title}</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏠 <b>Community Details:</b>
• <b>Name:</b> {scan_data.get('title', 'Unknown')}
• <b>ID:</b> <code>{scan_data.get('id', 'Unknown')}</code>
• <b>Type:</b> {scan_data.get('type', 'Unknown')}
• <b>Username:</b> {scan_data.get('username', 'None')}
• <b>Members:</b> {scan_data.get('members_count', 'Unknown')}
• <b>Description:</b> {scan_data.get('description', 'None')}

🛡️ <b>Security Status:</b>
• <b>Bot Role:</b> {'✅ Administrator' if scan_data.get('is_admin', False) else '❌ Member'}
• <b>Monitoring:</b> {'✅ Active' if scan_data.get('is_admin', False) else '⚠️ Limited'}
• <b>Protection:</b> {'✅ Enabled' if scan_data.get('is_admin', False) else '❌ Needs Admin'}
• <b>Risk Level:</b> {scan_data.get('risk_level', 'Unknown')}

📊 <b>Live Assessment:</b>
{scan_data.get('assessment', 'Initial scan completed.')}

💡 <b>Recommendations:</b>
{scan_data.get('recommendation', 'Ensure bot has admin permissions for full protection.')}

🕒 <b>Scan Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """
            else:
                # Simple notification for command usage
                notification = f"""
🔔 <b>{title}</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{details}

🕒 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """
            
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
            print(f"❌ Admin check error for chat {chat_id}: {e}")
            return False
    
    async def is_user_admin(self, context: CallbackContext, chat_id: int, user_id: int) -> bool:
        """Check if user is admin in the group/channel"""
        try:
            user_member = await context.bot.get_chat_member(chat_id, user_id)
            return user_member.status in ['administrator', 'creator']
        except Exception as e:
            print(f"❌ User admin check error: {e}")
            return False
    
    async def perform_live_scan(self, context: CallbackContext, chat_id: int, chat_title: str = None) -> dict:
        """Perform comprehensive live scan of community"""
        try:
            print(f"🔍 Starting live scan for chat {chat_id}")
            
            # Get basic chat information
            chat = await context.bot.get_chat(chat_id)
            members_count = await context.bot.get_chat_members_count(chat_id)
            
            # Check bot admin status
            is_admin = await self.is_bot_admin(context, chat_id)
            
            # Get community administrators count
            try:
                admins = await context.bot.get_chat_administrators(chat_id)
                admin_count = len([admin for admin in admins if not admin.user.is_bot])
            except:
                admin_count = "Unknown"
            
            # Comprehensive community data
            community_data = {
                'id': chat_id,
                'title': chat_title or chat.title,
                'type': chat.type,
                'username': f"@{chat.username}" if chat.username else "None",
                'members_count': members_count,
                'admin_count': admin_count,
                'description': chat.description or "None",
                'is_admin': is_admin,
                'scan_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'invite_link': chat.invite_link or "None"
            }
            
            # Generate security assessment
            assessment = await self.generate_security_assessment(context.bot, chat_id, is_admin, members_count)
            community_data.update(assessment)
            
            print(f"✅ Live scan completed for {community_data['title']}")
            return community_data
            
        except Exception as e:
            print(f"❌ Live scan failed: {e}")
            return {
                'id': chat_id,
                'title': chat_title or 'Unknown',
                'error': str(e),
                'assessment': '❌ Scan failed - Limited information available',
                'recommendation': 'Please ensure bot has access to community information.',
                'risk_level': 'UNKNOWN'
            }
    
    async def generate_security_assessment(self, bot, chat_id: int, is_admin: bool, members_count: int) -> dict:
        """Generate comprehensive security assessment"""
        try:
            risk_factors = []
            protections = []
            recommendations = []
            
            # Admin status assessment
            if not is_admin:
                risk_factors.append("❌ Bot lacks administrator permissions")
                recommendations.append("Make bot admin for full protection")
            else:
                protections.append("✅ Full administrative access")
                protections.append("✅ Complete monitoring capability")
                protections.append("✅ Auto-protection systems active")
            
            # Community type assessment
            chat = await bot.get_chat(chat_id)
            if chat.type == 'channel':
                risk_factors.append("📢 Channel - Limited member interaction monitoring")
                protections.append("✅ Content protection active")
                recommendations.append("Monitor for spam in channel posts")
            elif chat.type in ['group', 'supergroup']:
                protections.append("✅ Member activity monitoring")
                protections.append("✅ Message pattern analysis")
                protections.append("✅ User behavior tracking")
            
            # Member count risk assessment
            if members_count > 5000:
                risk_factors.append("🌐 Very large community - Higher spam risk")
                protections.append("✅ Scaled monitoring systems")
                recommendations.append("Implement strict moderation rules")
            elif members_count > 1000:
                risk_factors.append("👥 Large community - Elevated spam risk")
                protections.append("✅ Enhanced monitoring active")
            elif members_count > 100:
                protections.append("✅ Standard monitoring profile")
            else:
                protections.append("✅ Small community - Lower risk profile")
            
            # Determine overall risk level
            if not is_admin:
                risk_level = "🔴 HIGH RISK"
                analysis = "⚠️ <b>Limited Protection</b> - Admin permissions required for full security features."
                recommendations.append("Urgently make bot admin to enable protection")
            elif risk_factors:
                risk_level = "🟡 MEDIUM RISK"
                analysis = "🟡 <b>Protected with Concerns</b> - Community is monitored but has some risk factors."
                recommendations.append("Address risk factors for improved security")
            else:
                risk_level = "🟢 LOW RISK"
                analysis = "🟢 <b>Well Protected</b> - Community is secure with active monitoring systems."
                recommendations.append("Continue current protection levels")
            
            # Add general recommendations
            if is_admin:
                recommendations.append("Review weekly security reports")
                recommendations.append("Monitor alert notifications")
            recommendations.append("Keep bot updated with latest features")
            
            return {
                'risk_level': risk_level,
                'analysis': analysis,
                'recommendation': '\n'.join(f"• {rec}" for rec in recommendations),
                'risk_factors': risk_factors,
                'protections': protections
            }
            
        except Exception as e:
            return {
                'risk_level': "⚫ UNKNOWN",
                'analysis': f"❌ <b>Assessment Incomplete</b> - Error: {str(e)}",
                'recommendation': "Please ensure bot has proper access to community data and try again.",
                'risk_factors': ["Assessment failed"],
                'protections': ["Limited information available"]
            }

    # ===== ENHANCED COMMAND HANDLERS =====
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced start command with live scanning and private introduction"""
        user = update.effective_user
        chat = update.effective_chat
        chat_type = chat.type
        
        print(f"🎯 /start command from user {user.id} in {chat_type} chat {chat.id}")
        
        # Private chat - show full introduction and feature list
        if chat_type == 'private':
            welcome_text = """
🤖 <b>Community Protection Bot - Complete Introduction</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛡️ <b>Advanced Protection System</b>

I am an AI-powered security bot designed to protect your Telegram communities from threats, spam, and suspicious activities.

🚀 <b>Core Features:</b>

• <b>Live Community Scanning</b> - Real-time security assessment
• <b>Admin-Based Monitoring</b> - Full access when administrator
• <b>Automatic Threat Detection</b> - Spam, scams, risky behavior
• <b>Interactive Configuration</b> - Custom settings per community
• <b>Health Monitoring</b> - Track community safety status
• <b>Alert System</b> - Real-time threat notifications

📊 <b>Live Scanning Capabilities:</b>
✅ Complete community information & metrics
✅ Security risk assessment (LOW/MEDIUM/HIGH)  
✅ Member activity pattern analysis
✅ Protection status overview
✅ Automated security systems

⚙️ <b>Setup Process:</b>
1. Add me to your group/channel as administrator
2. I automatically perform initial security scan
3. Use /start in the community for live scanning
4. Configure settings with /settings command

🔧 <b>Available Commands:</b>

• <b>/start</b> - Start bot or perform live community scan
• <b>/help</b> - Detailed help guide and instructions
• <b>/stats</b> - View all active communities
• <b>/settings</b> - Configure protection settings
• <b>/alerts</b> - Check security alerts summary
• <b>/status</b> - Community health status check

🚀 <b>Get Started Now:</b>
Add me to a group/channel, make me admin, and use /start to begin live protection!

🔒 <b>Privacy & Security:</b>
All scan results and alerts are sent privately to the bot owner. Community members only see basic status information.
            """
            try:
                await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML)
                print("✅ Private welcome message sent successfully")
                
                # Notify owner about private start command
                user_info = {
                    'id': user.id,
                    'name': f"{user.first_name} {user.last_name or ''}".strip(),
                    'username': f"@{user.username}" if user.username else "None"
                }
                await self.notify_owner(
                    context,
                    "🔰 Private Start Command",
                    f"User {user_info['name']} ({user_info['username']}) started bot in private chat."
                )
                
            except Exception as e:
                print(f"❌ Failed to send welcome message: {e}")
        
        # Group/Channel - perform live scan if admin, show warning if not
        else:
            try:
                chat_title = chat.title
                user_name = f"{user.first_name} {user.last_name or ''}".strip()
                
                # Check if bot is admin for live scanning
                if await self.is_bot_admin(context, chat.id):
                    # Perform comprehensive live scan
                    processing_msg = await update.message.reply_text(
                        "🔍 <b>Performing Live Community Scan...</b>\n\n"
                        "Scanning security status, member activity, and protection systems...",
                        parse_mode=ParseMode.HTML
                    )
                    
                    # Perform the live scan
                    scan_data = await self.perform_live_scan(context, chat.id, chat_title)
                    
                    # Show quick results in the community
                    quick_result = f"""
✅ <b>Live Security Scan Complete</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏠 <b>Community:</b> {scan_data['title']}
📊 <b>Quick Overview:</b>
• 👥 Members: {scan_data['members_count']}
• 🎯 Type: {scan_data['type']}
• 🛡️ Status: {scan_data['risk_level']}
• 🔒 Protection: {'✅ Active' if scan_data['is_admin'] else '❌ Limited'}

📋 <b>Detailed security report has been sent to the bot owner.</b>

💡 <b>Next Steps:</b>
Continue monitoring with /status or configure settings with /settings
                    """
                    
                    await processing_msg.delete()
                    await update.message.reply_text(quick_result, parse_mode=ParseMode.HTML)
                    
                    # Send comprehensive report to owner
                    await self.notify_owner(
                        context, 
                        "🏠 Live Community Scan Results", 
                        f"Scan initiated by {user_name} (ID: {user.id}) in {chat_title}",
                        scan_data
                    )
                    
                    # Register/update community in database
                    try:
                        db.add_community(
                            chat.id, 
                            scan_data['title'], 
                            scan_data['type'], 
                            user.id
                        )
                        print(f"✅ Community registered/updated: {scan_data['title']}")
                    except Exception as e:
                        print(f"❌ Database registration failed: {e}")
                    
                else:
                    # Not admin - show comprehensive warning and explain required permissions
                    warning_msg = """
⚠️ <b>Administrator Access Required</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

I need administrator permissions to perform live community scanning and enable full protection features.

🔐 <b>Required Permissions:</b>

• <b>Read Messages</b> - For activity monitoring and threat detection
• <b>Delete Messages</b> - For automatic spam removal and content moderation  
• <b>Ban Users</b> - For immediate threat neutralization
• <b>Invite Users</b> - For community management and growth
• <b>Pin Messages</b> - For important security announcements

🚀 <b>Features Enabled with Admin Access:</b>

✅ Live community scanning & security assessment
✅ Automatic threat detection & response
✅ Real-time activity monitoring
✅ Security alert systems
✅ User behavior analysis
✅ Spam pattern recognition

🔧 <b>How to Enable:</b>
1. Go to group/channel settings
2. Select Administrators
3. Add this bot as administrator
4. Grant all recommended permissions
5. Use /start again to begin protection

📞 <b>Need Help?</b>
Contact the bot owner for setup assistance.
                    """
                    await update.message.reply_text(warning_msg, parse_mode=ParseMode.HTML)
                    
                    # Notify owner about access request
                    await self.notify_owner(
                        context,
                        "🔒 Admin Access Requested",
                        f"User {user_name} (ID: {user.id}) attempted security scan in \"{chat_title}\" but bot lacks admin permissions.\n\n"
                        f"Chat ID: <code>{chat.id}</code>\n"
                        f"Chat Type: {chat.type}"
                    )
                    
            except Exception as e:
                error_msg = """
❌ <b>Scan Error</b>

Unable to complete community security scan at this time. This could be due to:

• Temporary API limitations
• Network connectivity issues
• Permission conflicts

Please try again in a few moments or contact the bot owner for assistance.
                """
                await update.message.reply_text(error_msg, parse_mode=ParseMode.HTML)
                print(f"❌ Start command error in {chat_title}: {e}")
                
                # Notify owner about the error
                await self.notify_owner(
                    context,
                    "❌ Scan Error Occurred",
                    f"Error during scan in \"{chat_title}\": {str(e)}\n\n"
                    f"User: {user.first_name} (ID: {user.id})\n"
                    f"Chat ID: <code>{chat.id}</code>"
                )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send comprehensive help information"""
        help_text = """
🆘 <b>HAMSAS Protection Bot - Help Guide</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤖 <b>About This Bot:</b>
I am an advanced AI-powered security bot designed to protect Telegram communities from various threats including spam, scams, raids, and suspicious activities.

📋 <b>Available Commands:</b>

🔹 <b>/start</b> - Start the bot or perform live community security scan
• In private: Shows introduction and features
• In community: Performs live security scan (admin required)

🔹 <b>/help</b> - Show this comprehensive help guide

🔹 <b>/stats</b> - View all active communities and monitoring statistics

🔹 <b>/settings</b> - Configure bot features and protection settings

🔹 <b>/alerts</b> - Check security alerts and threat notifications

🔹 <b>/status</b> - View current community health and security status

🛡️ <b>Live Protection Features:</b>

• <b>Automatic Scanning</b> - Scans communities when bot is added
• <b>Real-time Monitoring</b> - Continuous threat detection
• <b>Security Assessment</b> - Risk level analysis (LOW/MEDIUM/HIGH)
• <b>Admin-Based Access</b> - Full features when administrator
• <b>Owner Notifications</b> - Private alerts and reports

⚙️ <b>Setup Requirements:</b>

• <b>Administrator Role</b> - Required for full protection features
• <b>Read Messages</b> - For activity monitoring
• <b>Delete Messages</b> - For spam removal
• <b>Ban Users</b> - For threat response

🔒 <b>Privacy Assurance:</b>
All detailed scan results and security alerts are sent privately to the bot owner. Community members only see basic status information.

📞 <b>Support:</b>
For technical issues or feature requests, contact the bot owner.

🚀 <b>Ready to Protect?</b>
Add me to your community, make me admin, and use /start to begin!
            """
        await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)
        
        # Notify owner about help command usage
        user = update.effective_user
        chat = update.effective_chat
        user_info = {
            'id': user.id,
            'name': f"{user.first_name} {user.last_name or ''}".strip(),
            'username': f"@{user.username}" if user.username else "None"
        }
        chat_info = {
            'id': chat.id,
            'title': chat.title or 'Private Chat',
            'type': chat.type
        }
        
        await self.notify_owner(
            context,
            "📖 Help Guide Accessed",
            f"User {user_info['name']} ({user_info['username']}) accessed help guide in {chat_info['type']} \"{chat_info['title']}\""
        )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show where bot is active with statistics"""
        try:
            # Get communities from database
            communities = db.get_all_communities()
            
            if not communities:
                stats_text = """
📊 <b>Bot Activity Statistics</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏠 <b>Active Communities:</b> 0
🚨 <b>Total Alerts:</b> 0
📈 <b>Monitoring Status:</b> Waiting for communities...

💡 <b>Getting Started:</b>
1. Add me to a group/channel
2. Make me administrator
3. I'll automatically register and begin monitoring
4. Use /start for live security scanning

🔍 <b>No communities are currently being monitored.</b>
                """
            else:
                total_alerts = db.get_total_alerts()
                active_monitoring = len([c for c in communities if c.get('is_active', True)])
                
                stats_text = f"""
📊 <b>Bot Activity Statistics</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏠 <b>Active Communities:</b> {len(communities)}
🔍 <b>Active Monitoring:</b> {active_monitoring}
🚨 <b>Total Alerts:</b> {total_alerts}
📈 <b>Protection Status:</b> ✅ Operational

🔎 <b>Recently Active Communities:</b>
"""
                # Show recent communities (max 8)
                for community in communities[:8]:
                    community_name = community.get('title', 'Unknown')[:20] + ('...' if len(community.get('title', '')) > 20 else '')
                    stats_text += f"• {community_name} ({community.get('type', 'group')})\n"
                
                if len(communities) > 8:
                    stats_text += f"• ... and {len(communities) - 8} more communities\n"
                
                stats_text += f"""
📋 <b>Summary:</b>
The bot is actively protecting {active_monitoring} out of {len(communities)} registered communities with {total_alerts} security alerts processed.
                """
            
            await update.message.reply_text(stats_text, parse_mode=ParseMode.HTML)
            
            # Notify owner
            user = update.effective_user
            chat = update.effective_chat
            await self.notify_owner(
                context,
                "📊 Statistics Viewed",
                f"User {user.first_name} viewed statistics in {chat.type} \"{chat.title or 'Private'}\"\n\n"
                f"Active Communities: {len(communities) if communities else 0}\n"
                f"Total Alerts: {total_alerts if 'total_alerts' in locals() else 0}"
            )
            
        except Exception as e:
            await update.message.reply_text("❌ Error fetching statistics. Please try again later.")
            print(f"❌ Stats command error: {e}")
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Configure bot features and protection settings"""
        chat = update.effective_chat
        user = update.effective_user
        
        # Check if user has permission to change settings
        if chat.type != 'private':
            if not await self.is_user_admin(context, chat.id, user.id):
                await update.message.reply_text(
                    "❌ <b>Permission Denied</b>\n\n"
                    "Only community administrators can configure bot settings.",
                    parse_mode=ParseMode.HTML
                )
                return
        
        settings_text = """
⚙️ <b>Bot Settings & Configuration Panel</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔧 <b>Interactive Configuration Features:</b>

The bot can be configured per community with the following settings:

• <b>Live Scanning Frequency</b> - How often to perform security scans
• <b>Monitoring Intensity</b> - Level of activity monitoring
• <b>Alert Preferences</b> - Types of notifications to receive
• <b>Auto-Protection Rules</b> - Automatic threat response actions
• <b>User Behavior Analysis</b> - Suspicious activity detection

🛠️ <b>Per-Community Settings:</b>

Each community can have customized protection settings:
- High security (strict monitoring)
- Medium security (balanced approach)  
- Low security (basic monitoring)

🔐 <b>Admin-Only Features:</b>

• Custom keyword filtering
• User restriction settings
• Moderation automation rules
• Alert escalation policies
• Report generation settings

🚀 <b>Current Default Settings:</b>

• Live Scanning: Enabled when admin
• Monitoring: Active for all communities
• Alerts: Real-time notifications
• Protection: Auto-enabled with admin access

💡 <b>Configuration Interface:</b>
Advanced configuration interface is under development. Currently, basic protection features are automatically enabled when the bot is administrator.

📞 <b>Custom Configuration:</b>
Contact the bot owner for custom security configuration and advanced feature setup.
        """
        
        await update.message.reply_text(settings_text, parse_mode=ParseMode.HTML)
        
        # Notify owner
        await self.notify_owner(
            context,
            "⚙️ Settings Accessed",
            f"User {user.first_name} (ID: {user.id}) accessed settings in {chat.type} \"{chat.title or 'Private'}\""
        )
    
    async def alerts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check security alerts and threat notifications"""
        try:
            # Get alerts summary from database
            alerts_data = db.get_alerts_summary()
            
            if not alerts_data:
                alerts_text = """
🚨 <b>Security Alerts Summary</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 <b>Total Alerts:</b> 0
🏠 <b>Monitored Communities:</b> 0
🔍 <b>Recent Activity:</b> No alerts recorded

🛡️ <b>Alert System Status:</b>
The security alert system is active and monitoring for threats. No alerts have been triggered yet.

💡 <b>When Alerts Appear:</b>
Alerts will appear here when the protection system detects:
• Suspicious messages or spam
• Unusual user behavior patterns
• Potential security threats
• System monitoring events

🔒 <b>Current Status:</b>
All monitored communities are secure with no active threats detected.
                """
            else:
                total_alerts = sum(item.get('alert_count', 0) for item in alerts_data)
                alert_communities = len(alerts_data)
                
                alerts_text = f"""
🚨 <b>Security Alerts Summary</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 <b>Total Alerts:</b> {total_alerts}
🏠 <b>Communities with Alerts:</b> {alert_communities}
🔍 <b>Monitoring Status:</b> ✅ Active

📋 <b>Alert Distribution:</b>
"""
                # Show communities with alerts
                for alert in alerts_data[:6]:
                    community_name = alert.get('chat_title', 'Unknown')[:25] + ('...' if len(alert.get('chat_title', '')) > 25 else '')
                    alert_count = alert.get('alert_count', 0)
                    alerts_text += f"• {community_name}: {alert_count} alert{'s' if alert_count != 1 else ''}\n"
                
                if len(alerts_data) > 6:
                    alerts_text += f"• ... and {len(alerts_data) - 6} more communities\n"
                
                alerts_text += f"""
📈 <b>Summary:</b>
The protection system has processed {total_alerts} security alerts across {alert_communities} communities.

🔒 <b>System Status:</b>
Real-time threat detection is active and monitoring all protected communities.
                """
            
            await update.message.reply_text(alerts_text, parse_mode=ParseMode.HTML)
            
            # Notify owner
            user = update.effective_user
            chat = update.effective_chat
            await self.notify_owner(
                context,
                "🚨 Alerts Summary Viewed",
                f"User {user.first_name} viewed alerts summary in {chat.type} \"{chat.title or 'Private'}\"\n\n"
                f"Total Alerts: {total_alerts if 'total_alerts' in locals() else 0}\n"
                f"Communities with Alerts: {alert_communities if 'alert_communities' in locals() else 0}"
            )
            
        except Exception as e:
            await update.message.reply_text("❌ Error fetching alerts. Please try again later.")
            print(f"❌ Alerts command error: {e}")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View current community health and security status"""
        chat = update.effective_chat
        user = update.effective_user
        
        try:
            # Check if in a community (not private chat)
            if chat.type == 'private':
                await update.message.reply_text(
                    "ℹ️ <b>Status Command Usage</b>\n\n"
                    "This command is designed to check the health and security status of a specific community.\n\n"
                    "Please use /status in a group or channel where I am a member to view its security status.",
                    parse_mode=ParseMode.HTML
                )
                return
            
            # Check if bot is admin (required for comprehensive scanning)
            if not await self.is_bot_admin(context, chat.id):
                await update.message.reply_text(
                    "⚠️ <b>Admin Permission Required</b>\n\n"
                    "I need administrator permissions to perform a comprehensive health scan of this community.\n\n"
                    "Please make me an administrator and try again, or use /start for basic community information.",
                    parse_mode=ParseMode.HTML
                )
                return
            
            # Perform health assessment scan
            processing_msg = await update.message.reply_text(
                "🔍 <b>Analyzing Community Health Status...</b>\n\n"
                "Scanning security systems, activity patterns, and protection status...",
                parse_mode=ParseMode.HTML
            )
            
            # Perform comprehensive scan
            scan_data = await self.perform_live_scan(context, chat.id, chat.title)
            
            # Generate status report
            status_report = f"""
📊 <b>Community Health Status Report</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏷️ <b>Community:</b> {scan_data['title']}
🆔 <b>ID:</b> <code>{scan_data['id']}</code>
📝 <b>Type:</b> {scan_data['type']}
👥 <b>Members:</b> {scan_data['members_count']}
👮 <b>Admins:</b> {scan_data['admin_count']}

{scan_data['analysis']}

💡 <b>Security Recommendations:</b>
{scan_data['recommendation']}

🛡️ <b>Active Protections:</b>
{chr(10).join(f"• {protection}" for protection in scan_data.get('protections', ['Basic monitoring active']))}

🕒 <b>Last Scan:</b> {scan_data['scan_time']}
            """
            
            await processing_msg.delete()
            await update.message.reply_text(status_report, parse_mode=ParseMode.HTML)
            
            # Notify owner
            await self.notify_owner(
                context,
                "📊 Status Check Completed",
                f"User {user.first_name} performed status check in \"{chat.title}\"\n\n"
                f"Status: {scan_data['risk_level']}\n"
                f"Members: {scan_data['members_count']}\n"
                f"Assessment: {scan_data['analysis'].split('<b>')[1].split('</b>')[0] if '<b>' in scan_data['analysis'] else 'Completed'}",
                scan_data
            )
            
        except Exception as e:
            await update.message.reply_text(
                "❌ <b>Status Check Failed</b>\n\n"
                "Unable to complete community health assessment. Please try again later.",
                parse_mode=ParseMode.HTML
            )
            print(f"❌ Status command error: {e}")
    
    async def handle_new_chat_members(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Automatic behavior when bot is added to group/channel"""
        new_members = update.message.new_chat_members
        bot_id = context.bot.id
        
        for member in new_members:
            if member.id == bot_id:
                # Bot was added to a community
                chat = update.effective_chat
                added_by = update.effective_user
                
                print(f"🎉 Bot added to new community: {chat.title} (ID: {chat.id}) by user {added_by.id}")
                
                try:
                    # Perform automatic comprehensive scan
                    scan_data = await self.perform_live_scan(context, chat.id, chat.title)
                    
                    # Register community in database
                    db.add_community(chat.id, chat.title, chat.type, added_by.id)
                    print(f"✅ Community registered in database: {chat.title}")
                    
                    # Send welcome message in the community
                    welcome_msg = f"""
🤖 <b>Community Protection Bot Activated</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Thank you for adding me to <b>{chat.title}</b>! I will help protect this community from spam, scams, and suspicious activities.

🚀 <b>Immediate Actions Taken:</b>

✅ Community registered in security system
✅ Initial security scan completed
✅ Basic monitoring activated
✅ Alert systems enabled

🔒 <b>Next Steps for Full Protection:</b>

1. <b>Make me Administrator</b> - Required for complete features
2. <b>Use /start command</b> - Perform comprehensive security scan
3. <b>Configure settings</b> - Use /settings for customization

🛡️ <b>Available Protection Features:</b>

• Live community scanning & assessment
• Automatic threat detection & response
• Real-time activity monitoring
• Security alert notifications
• User behavior analysis

⚡ <b>Current Status:</b>
Basic monitoring is active. Admin permissions will unlock full protection capabilities.

📞 <b>Need Help?</b>
Contact the bot owner for setup assistance or questions.
                    """
                    
                    await context.bot.send_message(
                        chat_id=chat.id,
                        text=welcome_msg,
                        parse_mode=ParseMode.HTML
                    )
                    
                    # Notify owner with comprehensive scan results
                    await self.notify_owner(
                        context,
                        "🆕 Bot Added to Community",
                        f"Added by: {added_by.first_name} (ID: {added_by.id})\n"
                        f"Community: {chat.title}\n"
                        f"Type: {chat.type}\n"
                        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        scan_data
                    )
                    
                    # Request admin permissions if not admin and it's a group/supergroup
                    if not scan_data['is_admin'] and chat.type in ['group', 'supergroup']:
                        await self.alert_system.request_admin_permissions(chat.id, bot_id)
                        
                        # Notify owner about admin request
                        await self.notify_owner(
                            context,
                            "📋 Admin Permissions Requested",
                            f"Auto-requested admin permissions for \"{chat.title}\"\n\n"
                            f"The bot has automatically requested administrator permissions to enable full protection features."
                        )
                        print(f"✅ Admin permissions requested for {chat.title}")
                    
                except Exception as e:
                    print(f"❌ Auto-setup failed for {chat.title}: {e}")
                    
                    # Notify owner of setup failure
                    await self.notify_owner(
                        context,
                        "❌ Auto-Setup Failed",
                        f"Failed to complete auto-setup in \"{chat.title}\": {str(e)}\n\n"
                        f"Added by: {added_by.first_name} (ID: {added_by.id})\n"
                        f"Chat ID: <code>{chat.id}</code>"
                    )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Monitor all messages for suspicious activities"""
        message = update.effective_message
        user = update.effective_user
        
        if not message or not user:
            return
        
        # Skip if message is from a bot
        if user.is_bot:
            return
        
        # Log message reception
        chat_title = message.chat.title or "Private Chat"
        print(f"💬 Message from {user.first_name} in {chat_title}: {message.text[:50] if message.text else 'Media message'}...")
        
        # Check for suspicious activities using the monitoring system
        suspicious_reasons = self.monitor.check_message(message)
        
        if suspicious_reasons:
            user_info = {
                'user_id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'timestamp': message.date.isoformat()
            }
            
            # Log the suspicious activity in database
            db.log_suspicious_activity(
                chat_id=message.chat_id,
                user_id=user.id,
                username=user.username,
                activity_type="suspicious_message",
                description=" | ".join(suspicious_reasons),
                message_content=message.text or message.caption or "Media content"
            )
            
            # Send alert to the community
            await self.alert_system.send_alert(
                chat_id=message.chat_id,
                user_info=user_info,
                reasons=suspicious_reasons,
                message_content=message.text or message.caption
            )
            
            # Notify owner about the suspicious activity
            chat_info = {
                'id': message.chat_id,
                'title': message.chat.title or 'Unknown Chat',
                'type': message.chat.type
            }
            
            await self.notify_owner(
                context,
                "🚨 Suspicious Activity Detected",
                f"User: {user.first_name} (ID: {user.id})\n"
                f"Community: {chat_info['title']}\n"
                f"Activity: {', '.join(suspicious_reasons)}\n"
                f"Content: {message.text or message.caption or 'Media message'}\n\n"
                f"Action: Alert sent to community and logged in database"
            )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors in the bot"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        try:
            # Notify bot owner about critical errors
            if self.config.OWNER_ID:
                error_msg = f"""
🚨 <b>Bot Error Notification</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ <b>Error Type:</b> {type(context.error).__name__}
📝 <b>Error Details:</b> {str(context.error)}
🕒 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🔧 <b>Update Info:</b>
{update if update else 'No update information available'}

💡 <b>Action:</b>
The error has been logged. Please check the application logs for complete details.
                """
                await context.bot.send_message(
                    chat_id=self.config.OWNER_ID,
                    text=error_msg,
                    parse_mode=ParseMode.HTML
                )
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")
    
    async def setup_commands(self, application):
        """Setup bot commands menu"""
        print("⚙️ Setting up bot commands...")
        commands = [
            BotCommand("start", "Start bot or perform live community scan"),
            BotCommand("help", "Show comprehensive help guide"),
            BotCommand("stats", "View active communities and statistics"),
            BotCommand("settings", "Configure protection settings"),
            BotCommand("alerts", "Check security alerts summary"),
            BotCommand("status", "View community health status"),
        ]
        await application.bot.set_my_commands(commands)
        print("✅ Bot commands setup complete")
    
    def run(self):
        """Start the bot"""
        print("\n🚀 Starting bot initialization...")
        
        # Validate configuration
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
            application.add_handler(CommandHandler("start", self.start_command))
            application.add_handler(CommandHandler("help", self.help_command))
            application.add_handler(CommandHandler("stats", self.stats_command))
            application.add_handler(CommandHandler("settings", self.settings_command))
            application.add_handler(CommandHandler("alerts", self.alerts_command))
            application.add_handler(CommandHandler("status", self.status_command))
            
            # Message handlers
            application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, self.handle_new_chat_members))
            application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, self.handle_message))
            
            # Error handler
            application.add_error_handler(self.error_handler)
            
            print("✅ All handlers added successfully")
            
            # Setup commands menu
            application.post_init = self.setup_commands
            
            print("\n" + "="*50)
            print("✅ BOT INITIALIZATION COMPLETE")
            print("🤖 Bot is starting...")
            print("📱 Send /start to your bot to test it")
            print("="*50 + "\n")
            
            # Start the bot
            print("🌐 Starting polling...")
            application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
                
        except Exception as e:
            print(f"❌ CRITICAL: Failed to start bot: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    try:
        bot = ProtectionBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
