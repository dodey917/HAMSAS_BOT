import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bot Token from @BotFather
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    # Your Telegram User ID (Bot owner)
    OWNER_ID = int(os.getenv('OWNER_ID', 0))
    
    # Database URL (Render provides DATABASE_URL)
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bot_data.db')
    
    # Suspicious activity patterns
    SUSPICIOUS_KEYWORDS = [
        'http://', 'https://', 't.me/', '.com', '.org', '.net',
        'bit.ly', 't.co', 'spam', 'scam', 'phishing'
    ]
    
    # Rate limiting thresholds
    MESSAGES_PER_MINUTE = 10
    LINKS_PER_HOUR = 5
    JOIN_REQUESTS_PER_MINUTE = 3
