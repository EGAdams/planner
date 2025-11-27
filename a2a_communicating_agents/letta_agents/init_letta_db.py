#!/usr/bin/env python3
"""Initialize Letta PostgreSQL database schema."""

import asyncio
import os
from sqlalchemy import text

# Set environment variable before importing Letta modules
os.environ['LETTA_PG_URI'] = 'postgresql+pg8000://letta:letta@localhost:5432/letta'

from letta.orm import Base
from letta.server.db import engine

async def init_db():
    """Initialize database schema."""
    print("🔧 Initializing Letta database schema...")
    print(f"📊 Database: {os.environ['LETTA_PG_URI']}")

    async with engine.begin() as conn:
        # Create all tables
        print("✨ Creating tables...")
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Database initialization complete!")

    # Verify tables were created
    async with engine.connect() as conn:
        result = await conn.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' ORDER BY table_name;"
        ))
        tables = [row[0] for row in result]
        print(f"\n📋 Created {len(tables)} tables:")
        for table in tables:
            print(f"   - {table}")

if __name__ == '__main__':
    asyncio.run(init_db())
