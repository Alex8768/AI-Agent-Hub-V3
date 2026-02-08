#!/usr/bin/env python3
"""
Seed test data for AI Agent Hub V3.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.infrastructure.database import get_db
from src.core.types import Document, DocumentChunk, DocumentMetadata
from src.core.config import settings


async def seed_documents():
    """Seed sample documents."""
    print("📄 Seeding sample documents...")
    
    async with get_db() as db:
        # Create sample documents
        documents = [
            Document(
                name="AI Research Paper.pdf",
                path="/documents/research/ai_paper.pdf",
                format="pdf",
                size=2048000,
                status="completed",
                metadata=DocumentMetadata(
                    title="Advances in Artificial Intelligence",
                    author="AI Research Team",
                    source="arXiv",
                    page_count=15,
                    keywords=["ai", "machine learning", "research"]
                )
            ),
            Document(
                name="Technical Report.docx",
                path="/documents/reports/tech_report.docx",
                format="docx",
                size=1024000,
                status="completed",
                metadata=DocumentMetadata(
                    title="Technical Architecture Overview",
                    author="Engineering Team",
                    page_count=8,
                    keywords=["architecture", "technical", "design"]
                )
            ),
            Document(
                name="Meeting Notes.md",
                path="/documents/notes/meeting_notes.md",
                format="md",
                size=51200,
                status="completed",
                metadata=DocumentMetadata(
                    title="Weekly Team Meeting",
                    author="Project Manager",
                    keywords=["meeting", "notes", "team"]
                )
            ),
        ]
        
        for doc in documents:
            await db.execute(
                """
                INSERT INTO documents (id, name, path, format, size, status, metadata, created_at, updated_at)
                VALUES (:id, :name, :path, :format, :size, :status, :metadata, :created_at, :updated_at)
                ON CONFLICT (id) DO NOTHING
                """,
                {
                    "id": doc.id,
                    "name": doc.name,
                    "path": doc.path,
                    "format": doc.format.value,
                    "size": doc.size,
                    "status": doc.status.value,
                    "metadata": json.dumps(doc.metadata.dict()),
                    "created_at": doc.created_at,
                    "updated_at": doc.updated_at,
                }
            )
        
        print(f"✅ Seeded {len(documents)} documents")


async def seed_users():
    """Seed sample users."""
    print("👤 Seeding sample users...")
    
    async with get_db() as db:
        users = [
            {
                "id": "user_001",
                "username": "admin",
                "email": "admin@aiagenthub.com",
                "role": "admin",
                "created_at": datetime.utcnow(),
            },
            {
                "id": "user_002",
                "username": "researcher",
                "email": "researcher@aiagenthub.com",
                "role": "researcher",
                "created_at": datetime.utcnow(),
            },
            {
                "id": "user_003",
                "username": "developer",
                "email": "developer@aiagenthub.com",
                "role": "developer",
                "created_at": datetime.utcnow(),
            },
        ]
        
        for user in users:
            await db.execute(
                """
                INSERT INTO users (id, username, email, role, created_at)
                VALUES (:id, :username, :email, :role, :created_at)
                ON CONFLICT (id) DO NOTHING
                """,
                user
            )
        
        print(f"✅ Seeded {len(users)} users")


async def main():
    """Main seed function."""
    print("🌱 Seeding AI Agent Hub V3 with sample data...")
    
    try:
        await seed_users()
        await seed_documents()
        
        print("🎉 Database seeding completed successfully!")
        
    except Exception as e:
        print(f"❌ Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
