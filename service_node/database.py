import asyncpg
from config import settings

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(dsn=settings.DATABASE_URL)
        await self.init_db()

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

    async def init_db(self):
        async with self.pool.acquire() as connection:
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    id SERIAL PRIMARY KEY,
                    agent_id VARCHAR(64) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    token VARCHAR(255) UNIQUE NOT NULL,
                    description TEXT,
                    capabilities JSONB,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS skills (
                    id SERIAL PRIMARY KEY,
                    skill_id VARCHAR(64) UNIQUE NOT NULL,
                    agent_id VARCHAR(64) REFERENCES agents(agent_id),
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    tags TEXT[],
                    version VARCHAR(50),
                    filename VARCHAR(255),
                    file_content BYTEA,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(name, version)
                );
            """)

db = Database()

async def get_db_pool():
    if not db.pool:
        await db.connect()
    return db.pool
