"""
Database module for Telegram analytics bot.
Handles PostgreSQL connection, table initialization, and data operations.
"""
import asyncpg
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Establish connection pool to PostgreSQL database."""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            logger.info("✅ Database connection pool established")
            await self.initialize_database()
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            raise

    async def initialize_database(self):
        """Create tables if they don't exist."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    platform TEXT DEFAULT 'telegram',
                    chat_id BIGINT,
                    user_id TEXT,
                    user_name TEXT,
                    message_text TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_messages_created_at 
                ON messages(created_at DESC);
                
                CREATE INDEX IF NOT EXISTS idx_messages_chat_id 
                ON messages(chat_id);
            """)
            logger.info("✅ Database tables initialized")
            
            # Run initial cleanup
            await self.cleanup_old_messages()

    async def cleanup_old_messages(self):
        """Delete messages older than 14 days."""
        cutoff_date = datetime.now() - timedelta(days=14)
        async with self.pool.acquire() as conn:
            deleted = await conn.execute(
                "DELETE FROM messages WHERE created_at < $1",
                cutoff_date
            )
            count = deleted.split()[-1]
            logger.info(f"🗑️ Cleanup completed: {count} old messages deleted")
            return int(count)

    async def insert_message(
        self,
        chat_id: int,
        user_id: str,
        user_name: str,
        message_text: str
    ):
        """Insert a new message into the database."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO messages (chat_id, user_id, user_name, message_text)
                VALUES ($1, $2, $3, $4)
            """, chat_id, user_id, user_name, message_text)

    async def get_messages_last_24h(self, chat_id: int) -> List[Dict]:
        """Retrieve all messages from the last 24 hours."""
        cutoff_time = datetime.now() - timedelta(hours=24)
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT user_id, user_name, message_text, created_at
                FROM messages
                WHERE chat_id = $1 AND created_at >= $2
                ORDER BY created_at ASC
            """, chat_id, cutoff_time)
            
            return [dict(row) for row in rows]

    async def get_messages_last_14_days(self, chat_id: int) -> List[Dict]:
        """Retrieve all messages from the last 14 days."""
        cutoff_time = datetime.now() - timedelta(days=14)
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT user_id, user_name, message_text, created_at
                FROM messages
                WHERE chat_id = $1 AND created_at >= $2
                ORDER BY created_at ASC
            """, chat_id, cutoff_time)
            
            return [dict(row) for row in rows]

    async def get_message_count(self, chat_id: int) -> int:
        """Get total message count for a chat."""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT COUNT(*) FROM messages WHERE chat_id = $1",
                chat_id
            )
            return result

    async def close(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
