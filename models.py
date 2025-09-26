"""
SQLAlchemy models for the Discord server archive bot.
"""

from sqlalchemy import (
    Column,
    String,
    BigInteger,
    DateTime,
    Index
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Attachment(Base):
    """Model for storing Discord attachment information."""

    __tablename__ = 'attachments'
    __table_args__ = (
        Index('idx_attachments_channel_id', 'channel_id'),
        Index('idx_attachments_message_date', 'message_date'),
        Index('idx_attachments_channel_message_date', 'channel_id', 'message_date'),
    )

    url = Column(String, primary_key=True, nullable=False)

    filename = Column(String, nullable=False)

    channel_id = Column(BigInteger, nullable=False)

    message_date = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"<Attachment(url='{self.url}', filename='{self.filename}', channel_id={self.channel_id})>"
