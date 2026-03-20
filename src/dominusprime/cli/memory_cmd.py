# -*- coding: utf-8 -*-
"""CLI commands for memory management."""

import asyncio
import json
from pathlib import Path
from typing import Optional

import click

from ..agents.memory.experience.system import ExperienceSystem
from ..agents.memory.multimodal.processor import MediaProcessor
from ..agents.memory.multimodal.index import MultimodalIndex
from ..database.connection import DatabaseManager


@click.group()
def memory():
    """Memory system management commands."""
    pass


@memory.command()
@click.option(
    "--db-path",
    type=click.Path(),
    default="./data/experiences.db",
    help="Path to experiences database",
)
def stats(db_path: str):
    """Show memory system statistics."""
    db_path = Path(db_path)
    
    if not db_path.exists():
        click.echo(f"❌ Database not found: {db_path}")
        return
    
    async def get_stats():
        # Initialize database
        db_manager = DatabaseManager(db_path.parent)
        await db_manager.initialize()
        
        # Get experience stats
        experiences_db = db_manager.get_connection("experiences")
        cursor = experiences_db.cursor()
        
        total_exp = cursor.execute("SELECT COUNT(*) FROM experiences").fetchone()[0]
        total_skills = cursor.execute("SELECT COUNT(*) FROM generated_skills").fetchone()[0]
        
        # Get multimodal stats
        multimodal_db = db_manager.get_connection("multimodal")
        cursor = multimodal_db.cursor()
        
        total_media = cursor.execute("SELECT COUNT(*) FROM media_items").fetchone()[0]
        total_embeddings = cursor.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
        
        return {
            "experiences": total_exp,
            "skills": total_skills,
            "media_items": total_media,
            "embeddings": total_embeddings,
        }
    
    stats_data = asyncio.run(get_stats())
    
    click.echo("\n📊 Memory System Statistics")
    click.echo("=" * 40)
    click.echo(f"  Experiences:     {stats_data['experiences']:>6}")
    click.echo(f"  Generated Skills: {stats_data['skills']:>6}")
    click.echo(f"  Media Items:     {stats_data['media_items']:>6}")
    click.echo(f"  Embeddings:      {stats_data['embeddings']:>6}")
    click.echo("=" * 40)


@memory.command()
@click.option(
    "--db-path",
    type=click.Path(),
    default="./data/experiences.db",
    help="Path to experiences database",
)
@click.option(
    "--limit",
    type=int,
    default=10,
    help="Number of experiences to show",
)
@click.option(
    "--type",
    "exp_type",
    type=click.Choice(["task", "preference", "error", "all"]),
    default="all",
    help="Filter by experience type",
)
def list_experiences(db_path: str, limit: int, exp_type: str):
    """List stored experiences."""
    db_path = Path(db_path)
    
    if not db_path.exists():
        click.echo(f"❌ Database not found: {db_path}")
        return
    
    async def get_experiences():
        db_manager = DatabaseManager(db_path.parent)
        await db_manager.initialize()
        
        experiences_db = db_manager.get_connection("experiences")
        cursor = experiences_db.cursor()
        
        query = "SELECT * FROM experiences"
        params = []
        
        if exp_type != "all":
            query += " WHERE pattern_type = ?"
            params.append(exp_type)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        rows = cursor.execute(query, params).fetchall()
        
        experiences = []
        for row in rows:
            experiences.append({
                "id": row[0],
                "type": row[1],
                "description": row[2],
                "confidence": row[3],
                "frequency": row[4],
                "created_at": row[7],
            })
        
        return experiences
    
    experiences = asyncio.run(get_experiences())
    
    if not experiences:
        click.echo("No experiences found.")
        return
    
    click.echo(f"\n📚 Recent Experiences (showing {len(experiences)})")
    click.echo("=" * 60)
    
    for exp in experiences:
        click.echo(f"\n  ID: {exp['id']}")
        click.echo(f"  Type: {exp['type']}")
        click.echo(f"  Description: {exp['description'][:100]}")
        click.echo(f"  Confidence: {exp['confidence']:.2f} | Frequency: {exp['frequency']}")
        click.echo(f"  Created: {exp['created_at']}")


@memory.command()
@click.option(
    "--db-path",
    type=click.Path(),
    default="./data/experiences.db",
    help="Path to experiences database",
)
@click.option(
    "--query",
    required=True,
    help="Search query",
)
@click.option(
    "--limit",
    type=int,
    default=5,
    help="Number of results",
)
def search(db_path: str, query: str, limit: int):
    """Search experiences."""
    db_path = Path(db_path)
    
    if not db_path.exists():
        click.echo(f"❌ Database not found: {db_path}")
        return
    
    async def search_experiences():
        db_manager = DatabaseManager(db_path.parent)
        await db_manager.initialize()
        
        experiences_db = db_manager.get_connection("experiences")
        cursor = experiences_db.cursor()
        
        # Simple text search
        rows = cursor.execute(
            """
            SELECT * FROM experiences
            WHERE description LIKE ? OR pattern_data LIKE ?
            ORDER BY confidence DESC, frequency DESC
            LIMIT ?
            """,
            (f"%{query}%", f"%{query}%", limit)
        ).fetchall()
        
        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "type": row[1],
                "description": row[2],
                "confidence": row[3],
                "frequency": row[4],
            })
        
        return results
    
    results = asyncio.run(search_experiences())
    
    if not results:
        click.echo(f"No experiences found matching '{query}'")
        return
    
    click.echo(f"\n🔍 Search Results for '{query}' ({len(results)} found)")
    click.echo("=" * 60)
    
    for result in results:
        click.echo(f"\n  {result['type'].upper()}: {result['description'][:80]}")
        click.echo(f"  Confidence: {result['confidence']:.2f} | Frequency: {result['frequency']}")
        click.echo(f"  ID: {result['id']}")


@memory.command()
@click.option(
    "--working-dir",
    type=click.Path(),
    default=".",
    help="Agent working directory",
)
def list_skills(working_dir: str):
    """List generated skills."""
    skills_dir = Path(working_dir) / "skills" / "learned"
    
    if not skills_dir.exists():
        click.echo(f"❌ Skills directory not found: {skills_dir}")
        return
    
    skill_files = list(skills_dir.glob("*.md"))
    
    if not skill_files:
        click.echo("No generated skills found.")
        return
    
    click.echo(f"\n🎓 Generated Skills ({len(skill_files)} found)")
    click.echo("=" * 60)
    
    for skill_file in sorted(skill_files):
        # Read first line for title
        with open(skill_file, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            title = first_line.replace('#', '').strip() if first_line.startswith('#') else skill_file.stem
        
        click.echo(f"  • {title}")
        click.echo(f"    File: {skill_file.name}")


@memory.command()
@click.option(
    "--db-path",
    type=click.Path(),
    default="./data/multimodal.db",
    help="Path to multimodal database",
)
@click.option(
    "--limit",
    type=int,
    default=10,
    help="Number of media items to show",
)
def list_media(db_path: str, limit: int):
    """List stored media items."""
    db_path = Path(db_path)
    
    if not db_path.exists():
        click.echo(f"❌ Database not found: {db_path}")
        return
    
    async def get_media():
        db_manager = DatabaseManager(db_path.parent)
        await db_manager.initialize()
        
        multimodal_db = db_manager.get_connection("multimodal")
        cursor = multimodal_db.cursor()
        
        rows = cursor.execute(
            """
            SELECT id, media_type, original_filename, file_size,
                   status, created_at
            FROM media_items
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()
        
        items = []
        for row in rows:
            items.append({
                "id": row[0],
                "type": row[1],
                "filename": row[2],
                "size": row[3],
                "status": row[4],
                "created": row[5],
            })
        
        return items
    
    items = asyncio.run(get_media())
    
    if not items:
        click.echo("No media items found.")
        return
    
    click.echo(f"\n🖼️  Stored Media Items (showing {len(items)})")
    click.echo("=" * 60)
    
    for item in items:
        size_kb = item['size'] / 1024
        click.echo(f"\n  {item['type'].upper()}: {item['filename']}")
        click.echo(f"  Size: {size_kb:.1f} KB | Status: {item['status']}")
        click.echo(f"  ID: {item['id']} | Created: {item['created']}")


@memory.command()
@click.confirmation_option(prompt="Are you sure you want to clear all memory data?")
@click.option(
    "--data-dir",
    type=click.Path(),
    default="./data",
    help="Data directory",
)
def clear(data_dir: str):
    """Clear all memory data (DANGER!)."""
    data_path = Path(data_dir)
    
    # Delete database files
    databases = [
        "experiences.db",
        "multimodal.db",
        "security.db",
    ]
    
    deleted = []
    for db_name in databases:
        db_file = data_path / db_name
        if db_file.exists():
            db_file.unlink()
            deleted.append(db_name)
    
    if deleted:
        click.echo(f"✅ Deleted: {', '.join(deleted)}")
    else:
        click.echo("No databases found to delete.")


if __name__ == "__main__":
    memory()
