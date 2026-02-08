#!/usr/bin/env python3
"""
Database initialization script for AI Agent Hub V3.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.infrastructure.database import init_database, create_tables
from src.core.config import settings


async def main():
    """Initialize database."""
    print("🚀 Initializing AI Agent Hub V3 database...")
    print(f"📊 Database URL: {settings.database_url}")
    
    try:
        # Initialize database connection
        await init_database()
        
        # Create tables
        await create_tables()
        
        print("✅ Database initialized successfully!")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
