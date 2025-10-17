import re
from datetime import datetime, timedelta
from collections import defaultdict
from database import Session, SuspiciousActivity, Community
import config

class ActivityMonitor:
    def __init__(self):
        self.user_message_count = defaultdict(int)
        self.user_link_count = defaultdict(int)
        self.last_reset = datetime.utcnow()
        self.suspicious_patterns = config.Config.SUSPICIOUS_KEYWORDS
        
    def reset_counters(self):
        """Reset counters periodically"""
        current_time = datetime.utcnow()
        if current_time - self.last_reset > timedelta(minutes=1):
            self.user_message_count.clear()
            self.user_link_count.clear()
            self.last_reset = current_time
    
    def check_message(self, message):
        """Check a message for suspicious activity"""
        self.reset_counters()
        
        user_id = str(message.from_user.id)
        chat_id = str(message.chat_id)
        text = message.text or message.caption or ""
        
        suspicious_reasons = []
        
        # Rate limiting check
        self.user_message_count[user_id] += 1
        if self.user_message_count[user_id] > config.Config.MESSAGES_PER_MINUTE:
            suspicious_reasons.append(f"Message flood: {self.user_message_count[user_id]} messages per minute")
        
        # Link detection
        links = self.extract_links(text)
        if links:
            self.user_link_count[user_id] += len(links)
            if self.user_link_count[user_id] > config.Config.LINKS_PER_HOUR:
                suspicious_reasons.append(f"Excessive links: {self.user_link_count[user_id]} links per hour")
            
            # Check for suspicious URLs
            for link in links:
                if self.is_suspicious_url(link):
                    suspicious_reasons.append(f"Suspicious URL detected: {link}")
        
        # Keyword detection
        for keyword in config.Config.SUSPICIOUS_KEYWORDS:
            if keyword.lower() in text.lower():
                suspicious_reasons.append(f"Suspicious keyword detected: {keyword}")
        
        # Spam pattern detection
        if self.detect_spam_patterns(text):
            suspicious_reasons.append("Spam-like message pattern detected")
        
        return suspicious_reasons
    
    def extract_links(self, text):
        """Extract URLs from text"""
        if not text:
            return []
        
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return re.findall(url_pattern, text)
    
    def is_suspicious_url(self, url):
        """Check if URL is suspicious"""
        suspicious_domains = ['bit.ly', 't.co', 'tinyurl.com', 'shorte.st']
        return any(domain in url for domain in suspicious_domains)
    
    def detect_spam_patterns(self, text):
        """Detect spam patterns in text"""
        if not text:
            return False
        
        # Check for excessive capitalization
        if len(text) > 10 and sum(1 for c in text if c.isupper()) / len(text) > 0.7:
            return True
        
        # Check for repetitive patterns
        words = text.split()
        if len(words) > 5 and len(set(words)) / len(words) < 0.3:
            return True
        
        return False
    
    def log_activity(self, chat_id, user_id, username, activity_type, description, message_content=""):
        """Log suspicious activity to database"""
        session = Session()
        try:
            activity = SuspiciousActivity(
                chat_id=str(chat_id),
                user_id=str(user_id),
                username=username,
                activity_type=activity_type,
                description=description,
                message_content=message_content
            )
            session.add(activity)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error logging activity: {e}")
        finally:
            session.close()
