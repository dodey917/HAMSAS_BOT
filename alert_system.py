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
        except Exception as e:
            print("❌ AlertSystem: Failed to initialize bot: {}".format(e))
            self.bot = None
            
        self.cooldown_users = set()
        print("✅ Alert System ready")
    
    async def send_alert(self, chat_id, user_info, reasons, message_content=""):
        # ... rest of your existing send_alert method ...
    
    async def request_admin_permissions(self, chat_id, bot_id):
        # ... rest of your existing request_admin_permissions method ...
