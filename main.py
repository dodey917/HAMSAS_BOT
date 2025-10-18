import os
import logging
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import sqlite3
from datetime import datetime, timedelta
import asyncio

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token from environment variable
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Database setup
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    # Create tables for group statistics and activity tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS group_stats (
            group_id INTEGER PRIMARY KEY,
            group_title TEXT,
            member_count INTEGER,
            active_members INTEGER,
            last_updated TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS group_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER,
            message_count INTEGER,
            active_users INTEGER,
            date DATE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_activity (
            user_id INTEGER,
            group_id INTEGER,
            last_active TIMESTAMP,
            message_count INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, group_id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    if update.effective_chat.type == "private":
        await update.message.reply_text(
            "🤖 HAMSAS Bot is running!\n\n"
            "Available commands:\n"
            "/start - Live scanning in groups, introduction in private\n"
            "/status - Community health checks\n"
            "/stats - Community statistics\n\n"
            "I can monitor group activity and provide member statistics even without admin rights!"
        )
    else:
        # In groups, start live scanning mode
        await update.message.reply_text(
            "🔍 HAMSAS Bot is now live scanning this group!\n"
            "I'll monitor activity and can provide statistics using /stats command."
        )
        # Start background scanning for this group
        asyncio.create_task(live_scan_group(update.effective_chat.id, context.bot))

async def live_scan_group(group_id: int, bot):
    """Background task to scan group activity"""
    while True:
        try:
            # Update group statistics
            await update_group_stats(group_id, bot)
            # Wait 5 minutes between scans
            await asyncio.sleep(300)
        except Exception as e:
            logger.error(f"Error in live scan for group {group_id}: {e}")
            break

async def update_group_stats(group_id: int, bot):
    """Update group member count and activity statistics"""
    try:
        # Get basic chat information
        chat = await bot.get_chat(group_id)
        member_count = await bot.get_chat_member_count(group_id)
        
        # Calculate active members (users who sent messages in last 24 hours)
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
        cursor.execute(
            'SELECT COUNT(DISTINCT user_id) FROM user_activity WHERE group_id = ? AND last_active > ?',
            (group_id, twenty_four_hours_ago)
        )
        active_members = cursor.fetchone()[0] or 0
        
        # Update group stats
        cursor.execute('''
            INSERT OR REPLACE INTO group_stats 
            (group_id, group_title, member_count, active_members, last_updated)
            VALUES (?, ?, ?, ?, ?)
        ''', (group_id, chat.title, member_count, active_members, datetime.now()))
        
        # Update daily activity
        today = datetime.now().date()
        cursor.execute(
            'SELECT message_count FROM group_activity WHERE group_id = ? AND date = ?',
            (group_id, today)
        )
        result = cursor.fetchone()
        
        if result:
            cursor.execute(
                'UPDATE group_activity SET message_count = message_count + 1 WHERE group_id = ? AND date = ?',
                (group_id, today)
            )
        else:
            cursor.execute(
                'INSERT INTO group_activity (group_id, message_count, active_users, date) VALUES (?, 1, ?, ?)',
                (group_id, active_members, today)
            )
        
        conn.commit()
        conn.close()
        
        logger.info(f"Updated stats for group {chat.title}: {member_count} members, {active_members} active")
        
    except Exception as e:
        logger.error(f"Error updating group stats for {group_id}: {e}")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Community health check"""
    chat_id = update.effective_chat.id
    
    if update.effective_chat.type == "private":
        await update.message.reply_text("❌ This command works in groups only!")
        return
    
    try:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        
        # Get current group stats
        cursor.execute(
            'SELECT member_count, active_members, last_updated FROM group_stats WHERE group_id = ?',
            (chat_id,)
        )
        result = cursor.fetchone()
        
        if not result:
            await update.message.reply_text("📊 No data available yet. I need some time to collect statistics.")
            return
        
        member_count, active_members, last_updated = result
        
        # Calculate activity rate
        activity_rate = (active_members / member_count * 100) if member_count > 0 else 0
        
        # Get today's message count
        today = datetime.now().date()
        cursor.execute(
            'SELECT SUM(message_count) FROM group_activity WHERE group_id = ? AND date = ?',
            (chat_id, today)
        )
        today_messages = cursor.fetchone()[0] or 0
        
        # Health assessment
        if activity_rate >= 50:
            health_status = "💚 Excellent"
        elif activity_rate >= 30:
            health_status = "💛 Good"
        elif activity_rate >= 15:
            health_status = "🟡 Moderate"
        else:
            health_status = "🔴 Needs Attention"
        
        response = (
            f"🏥 **Community Health Check**\n\n"
            f"**Group Status:** {health_status}\n"
            f"**Total Members:** {member_count}\n"
            f"**Active Members (24h):** {active_members}\n"
            f"**Activity Rate:** {activity_rate:.1f}%\n"
            f"**Today's Messages:** {today_messages}\n"
            f"**Last Updated:** {last_updated}\n\n"
            f"*Active members are users who sent messages in the last 24 hours*"
        )
        
        await update.message.reply_text(response)
        
    except Exception as e:
        logger.error(f"Error in status command: {e}")
        await update.message.reply_text("❌ Error retrieving status information")
    finally:
        conn.close()

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Community statistics"""
    chat_id = update.effective_chat.id
    
    if update.effective_chat.type == "private":
        await update.message.reply_text("❌ This command works in groups only!")
        return
    
    try:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        
        # Get current group stats
        cursor.execute(
            'SELECT member_count, active_members, last_updated FROM group_stats WHERE group_id = ?',
            (chat_id,)
        )
        result = cursor.fetchone()
        
        if not result:
            await update.message.reply_text("📊 No statistics available yet. I need some time to collect data.")
            return
        
        member_count, active_members, last_updated = result
        
        # Get weekly activity trend
        week_ago = (datetime.now() - timedelta(days=7)).date()
        cursor.execute('''
            SELECT date, message_count, active_users 
            FROM group_activity 
            WHERE group_id = ? AND date >= ? 
            ORDER BY date DESC 
            LIMIT 7
        ''', (chat_id, week_ago))
        
        weekly_data = cursor.fetchall()
        
        # Calculate weekly totals
        weekly_messages = sum(row[1] for row in weekly_data)
        avg_daily_active = sum(row[2] for row in weekly_data) / len(weekly_data) if weekly_data else 0
        
        response = (
            f"📈 **Community Statistics**\n\n"
            f"**Total Members:** {member_count}\n"
            f"**Currently Active:** {active_members}\n"
            f"**Weekly Messages:** {weekly_messages}\n"
            f"**Avg Daily Active Users:** {avg_daily_active:.1f}\n\n"
            f"**Recent Activity:**\n"
        )
        
        for date, messages, active_users in weekly_data[-3:]:  # Last 3 days
            response += f"• {date}: {messages} msgs, {active_users} active users\n"
        
        response += f"\n*Last updated: {last_updated}*"
        
        await update.message.reply_text(response)
        
    except Exception as e:
        logger.error(f"Error in stats command: {e}")
        await update.message.reply_text("❌ Error retrieving statistics")
    finally:
        conn.close()

async def track_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Track user activity when messages are sent"""
    if not update.message or not update.effective_user:
        return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    if update.effective_chat.type not in ["group", "supergroup"]:
        return
    
    try:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        
        # Update user activity
        cursor.execute('''
            INSERT OR REPLACE INTO user_activity 
            (user_id, group_id, last_active, message_count)
            VALUES (?, ?, ?, COALESCE((SELECT message_count FROM user_activity WHERE user_id = ? AND group_id = ?), 0) + 1)
        ''', (user_id, chat_id, datetime.now(), user_id, chat_id))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error tracking message: {e}")

async def post_init(application: Application):
    """Post initialization - set bot commands"""
    commands = [
        BotCommand("start", "Live scanning in groups, introduction in private"),
        BotCommand("status", "Community health checks"),
        BotCommand("stats", "Community statistics"),
    ]
    await application.bot.set_my_commands(commands)

def main():
    """Start the bot."""
    if not BOT_TOKEN:
        raise ValueError("No BOT_TOKEN environment variable set")
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("stats", stats))
    
    # Add message handler for tracking activity (handle all text messages except commands)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        track_message
    ))

    # Start the Bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
