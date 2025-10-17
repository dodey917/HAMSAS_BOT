from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import config

Base = declarative_base()

class Community(Base):
    __tablename__ = 'communities'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(String(100), unique=True, nullable=False)
    chat_title = Column(String(255))
    chat_type = Column(String(50))  # 'group', 'channel', 'supergroup'
    is_bot_admin = Column(Boolean, default=False)
    has_full_permissions = Column(Boolean, default=False)
    owner_id = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

class SuspiciousActivity(Base):
    __tablename__ = 'suspicious_activities'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(String(100), nullable=False)
    user_id = Column(String(100), nullable=False)
    username = Column(String(100))
    activity_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    message_content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)

class AlertSettings(Base):
    __tablename__ = 'alert_settings'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(String(100), unique=True, nullable=False)
    alert_owner = Column(Boolean, default=True)
    alert_admins = Column(Boolean, default=False)
    cooldown_minutes = Column(Integer, default=5)

# Database setup
engine = create_engine(config.Config.DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
