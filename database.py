import sqlite3
import json
from datetime import datetime
import os
import config

print("🗄️  Initializing database...")

class Database:
    def __init__(self):
        self.config = config.Config()
        self.db_path = self._get_db_path()
        print("💾 Database path: {}".format(self.db_path))
        self.init_database()
    
    def _get_db_path(self):
        """Get database path from environment or use default"""
        db_url = self.config.DATABASE_URL
        
        if db_url.startswith('sqlite:///'):
            return db_url.replace('sqlite:///', '')
        elif db_url.startswith('postgresql://'):
            print("⚠️  PostgreSQL detected, but using SQLite for simplicity")
            return 'bot_data.db'
        else:
            return db_url or 'bot_data.db'
    
    def init_database(self):
        """Initialize database tables"""
        print("📊 Creating database tables...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Communities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS communities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT UNIQUE NOT NULL,
                chat_title TEXT,
                chat_type TEXT,
                is_bot_admin BOOLEAN DEFAULT 0,
                has_full_permissions BOOLEAN DEFAULT 0,
                owner_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Created 'communities' table")
        
        # Suspicious activities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suspicious_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                username TEXT,
                activity_type TEXT NOT NULL,
                description TEXT NOT NULL,
                message_content TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved BOOLEAN DEFAULT 0
            )
        ''')
        print("✅ Created 'suspicious_activities' table")
        
        # Alert settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alert_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT UNIQUE NOT NULL,
                alert_owner BOOLEAN DEFAULT 1,
                alert_admins BOOLEAN DEFAULT 0,
                cooldown_minutes INTEGER DEFAULT 5
            )
        ''')
        print("✅ Created 'alert_settings' table")
        
        conn.commit()
        
        # Count existing records
        cursor.execute("SELECT COUNT(*) FROM communities")
        community_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM suspicious_activities")
        activity_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM alert_settings")
        settings_count = cursor.fetchone()[0]
        
        conn.close()
        
        print("📈 Database stats:")
        print("   Communities: {}".format(community_count))
        print("   Suspicious activities: {}".format(activity_count))
        print("   Alert settings: {}".format(settings_count))
        print("✅ Database initialization complete!\n")
    
    def add_community(self, chat_id, chat_title, chat_type, owner_id):
        """Add a new community to database"""
        print("➕ Adding community: {} (Type: {})".format(chat_title, chat_type))
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO communities 
                (chat_id, chat_title, chat_type, owner_id) 
                VALUES (?, ?, ?, ?)
            ''', (str(chat_id), chat_title, chat_type, str(owner_id)))
            conn.commit()
            print("✅ Community added successfully")
            return True
        except Exception as e:
            print("❌ Error adding community: {}".format(e))
            return False
        finally:
            conn.close()
    
    def log_suspicious_activity(self, chat_id, user_id, username, activity_type, description, message_content=""):
        """Log suspicious activity"""
        print("⚠️  Logging suspicious activity from user: {}".format(username))
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO suspicious_activities 
                (chat_id, user_id, username, activity_type, description, message_content) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (str(chat_id), str(user_id), username, activity_type, description, message_content))
            conn.commit()
            print("✅ Activity logged successfully")
            return True
        except Exception as e:
            print("❌ Error logging activity: {}".format(e))
            return False
        finally:
            conn.close()
    
    def get_community_owner(self, chat_id):
        """Get community owner ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT owner_id FROM communities WHERE chat_id = ?', (str(chat_id),))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            print("👑 Found community owner: {}".format(result[0]))
        else:
            print("❌ No owner found for chat: {}".format(chat_id))
        
        return result[0] if result else None

# Create global database instance
print("🔨 Creating database instance...")
db = Database()
print("✅ Database module loaded successfully!\n")
