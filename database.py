import sqlite3
import logging
from pathlib import Path
import threading
from contextlib import contextmanager


class DatabaseManager:
    """Simple SQLite database for tracking downloaded attachments."""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger('bot.database')
        self._local = threading.local()
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a thread-local database connection."""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
        return self._local.connection
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database operations."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
    
    def _init_database(self):
        """Initialize the simple database schema."""
        with self.get_cursor() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attachments (
                    url TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    channel_id INTEGER NOT NULL,
                    download_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        self.logger.info('Database initialized successfully')
    
    def is_downloaded(self, url: str) -> bool:
        """Check if an attachment URL has already been downloaded."""
        with self.get_cursor() as cursor:
            cursor.execute('SELECT 1 FROM attachments WHERE url = ? LIMIT 1', (url,))
            return cursor.fetchone() is not None
    
    def add_attachment(self, url: str, filename: str, channel_id: int) -> bool:
        """Add a new attachment record to the database."""
        try:
            with self.get_cursor() as cursor:
                cursor.execute('''
                    INSERT INTO attachments (url, filename, channel_id)
                    VALUES (?, ?, ?)
                ''', (url, filename, channel_id))
            return True
        except sqlite3.IntegrityError:
            self.logger.debug(f'Attachment already exists in database: {url}')
            return False
        except Exception as e:
            self.logger.error(f'Error adding attachment to database: {e}')
            return False
    
    def close(self):
        """Close database connections."""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
