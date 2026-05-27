import os
import asyncio
import asyncpg

async def init():
    db_url = os.getenv("DATABASE_URL", "postgresql://jua:jua_secret@localhost:5432/jua_db")
    conn = await asyncpg.connect(db_url)
    try:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("pgvector extension ready")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(init())