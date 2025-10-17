import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
        self._check_environment_variables()
    
    def _check_environment_variables(self):
        """Check and log all required environment variables"""
        print("🔧 Checking environment variables...")
        
        # Bot Token from @BotFather
        self.BOT_TOKEN = os.getenv('BOT_TOKEN')
        if self.BOT_TOKEN:
            print("✅ BOT_TOKEN: Found (first 10 chars: {}...)".format(self.BOT_TOKEN[:10]))
        else:
            print("❌ BOT_TOKEN: Missing! Get it from @BotFather")
        
        # Your Telegram User ID (Bot owner)
        owner_id = os.getenv('OWNER_ID', '0')
        try:
            self.OWNER_ID = int(owner_id)
            print("✅ OWNER_ID: {}".format(self.OWNER_ID))
        except ValueError:
            self.OWNER_ID = 0
            print("❌ OWNER_ID: Invalid! Should be a number. Current: {}".format(owner_id))
        
        # Database URL (Render provides DATABASE_URL)
        self.DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bot_data.db')
        print("✅ DATABASE_URL: {}".format(self.DATABASE_URL))
        
        # Check if running on Render
        self.IS_RENDER = os.getenv('RENDER') is not None
        if self.IS_RENDER:
            print("🚀 Running on: Render.com")
        else:
            print("💻 Running on: Local environment")
        
        # Print all environment variables (except sensitive ones)
        print("\n📋 All environment variables:")
        for key, value in os.environ.items():
            if 'TOKEN' in key or 'SECRET' in key or 'KEY' in key:
                print("   {}: [HIDDEN]".format(key))
            else:
                print("   {}: {}".format(key, value))
        
        print("\n" + "="*50)
    
    # Suspicious activity patterns
    SUSPICIOUS_KEYWORDS = [
        'http://', 'https://', 't.me/', '.com', '.org', '.net',
        'bit.ly', 't.co', 'spam', 'scam', 'phishing'
    ]
    
    # Rate limiting thresholds
    MESSAGES_PER_MINUTE = 10
    LINKS_PER_HOUR = 5
    JOIN_REQUESTS_PER_MINUTE = 3
