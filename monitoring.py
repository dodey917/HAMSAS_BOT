import re
from datetime import datetime, timedelta
from collections import defaultdict
from database import db
import config

print("👀 Initializing Activity Monitor...")

class ActivityMonitor:
    def __init__(self):
        self.config = config.Config()
        self.user_message_count = defaultdict(int)
        self.user_link_count = defaultdict(int)
        self.last_reset = datetime.utcnow()
        self.suspicious_patterns = self.config.SUSPICIOUS_KEYWORDS
        
        print("✅ Activity Monitor initialized")
        print("   Suspicious keywords: {}".format(len(self.suspicious_patterns)))
        print("   Rate limits: {} msgs/min, {} links/hour".format(
            self.config.MESSAGES_PER_MINUTE, self.config.LINKS_PER_HOUR))
        
    def reset_counters(self):
        """Reset counters periodically"""
        current_time = datetime.utcnow()
        if current_time - self.last_reset > timedelta(minutes=1):
            if self.user_message_count or self.user_link_count:
                print("🔄 Resetting rate limit counters")
            self.user_message_count.clear()
            self.user_link_count.clear()
            self.last_reset = current_time
    
    def check_message(self, message):
        """Check a message for suspicious activity"""
        self.reset_counters()
        
        user_id = str(message.from_user.id)
        chat_id = str(message.chat_id)
        text = message.text or message.caption or ""
        
        print("🔍 Checking message from user {} in chat {}".format(user_id, chat_id))
        
        suspicious_reasons = []
        
        # Rate limiting check
        self.user_message_count[user_id] += 1
        current_count = self.user_message_count[user_id]
        print("   Message count for user {}: {}/{}".format(
            user_id, current_count, self.config.MESSAGES_PER_MINUTE))
        
        if current_count > self.config.MESSAGES_PER_MINUTE:
            reason = "Message flood: {} messages per minute".format(current_count)
            suspicious_reasons.append(reason)
            print("   ⚠️  {}".format(reason))
        
        # Link detection
        links = self.extract_links(text)
        if links:
            self.user_link_count[user_id] += len(links)
            current_links = self.user_link_count[user_id]
            print("   Link count for user {}: {}/{}".format(
                user_id, current_links, self.config.LINKS_PER_HOUR))
            
            if current_links > self.config.LINKS_PER_HOUR:
                reason = "Excessive links: {} links per hour".format(current_links)
                suspicious_reasons.append(reason)
                print("   ⚠️  {}".format(reason))
            
            # Check for suspicious URLs
            for link in links:
                if self.is_suspicious_url(link):
                    reason = "Suspicious URL detected: {}".format(link)
                    suspicious_reasons.append(reason)
                    print("   ⚠️  {}".format(reason))
        
        # Keyword detection
        for keyword in self.suspicious_patterns:
            if keyword.lower() in text.lower():
                reason = "Suspicious keyword detected: {}".format(keyword)
                suspicious_reasons.append(reason)
                print("   ⚠️  {}".format(reason))
                break  # Only report first match
        
        # Spam pattern detection
        if self.detect_spam_patterns(text):
            reason = "Spam-like message pattern detected"
            suspicious_reasons.append(reason)
            print("   ⚠️  {}".format(reason))
        
        if suspicious_reasons:
            print("   🚨 Total suspicious reasons: {}".format(len(suspicious_reasons)))
        else:
            print("   ✅ Message appears normal")
        
        return suspicious_reasons
    
    def extract_links(self, text):
        """Extract URLs from text"""
        if not text:
            return []
        
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        links = re.findall(url_pattern, text)
        
        if links:
            print("   🔗 Found {} links in message".format(len(links)))
        
        return links
    
    def is_suspicious_url(self, url):
        """Check if URL is suspicious"""
        suspicious_domains = ['bit.ly', 't.co', 'tinyurl.com', 'shorte.st']
        is_suspicious = any(domain in url for domain in suspicious_domains)
        
        if is_suspicious:
            print("   🚩 Suspicious URL: {}".format(url))
        
        return is_suspicious
    
    def detect_spam_patterns(self, text):
        """Detect spam patterns in text"""
        if not text:
            return False
        
        # Check for excessive capitalization
        if len(text) > 10:
            upper_ratio = sum(1 for c in text if c.isupper()) / len(text)
            if upper_ratio > 0.7:
                print("   🚩 Excessive capitalization: {:.1%}".format(upper_ratio))
                return True
        
        # Check for repetitive patterns
        words = text.split()
        if len(words) > 5:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.3:
                print("   🚩 Repetitive content: {:.1%} unique words".format(unique_ratio))
                return True
        
        return False

print("✅ Monitoring module loaded successfully!\n")
