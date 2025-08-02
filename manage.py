#!/usr/bin/env python3
"""
Management script for NoSugar Bot
"""
import asyncio
import sys
from pathlib import Path

from alembic.config import Config
from alembic import command

from database.connection import create_tables, drop_tables
from config import settings


def run_alembic_command(cmd, *args):
    """Run alembic command."""
    alembic_cfg = Config("alembic.ini")
    getattr(command, cmd)(alembic_cfg, *args)


async def init_db():
    """Initialize database tables."""
    print("Creating database tables...")
    try:
        await create_tables()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        sys.exit(1)


async def reset_db():
    """Reset database (drop all tables)."""
    print("Dropping all database tables...")
    try:
        await drop_tables()
        print("✅ Database tables dropped successfully")
    except Exception as e:
        print(f"❌ Error dropping tables: {e}")
        sys.exit(1)


def create_migration(message):
    """Create a new migration."""
    print(f"Creating migration: {message}")
    try:
        run_alembic_command("revision", "--autogenerate", "-m", message)
        print("✅ Migration created successfully")
    except Exception as e:
        print(f"❌ Error creating migration: {e}")
        sys.exit(1)


def upgrade_db():
    """Upgrade database to latest migration."""
    print("Upgrading database...")
    try:
        run_alembic_command("upgrade", "head")
        print("✅ Database upgraded successfully")
    except Exception as e:
        print(f"❌ Error upgrading database: {e}")
        sys.exit(1)


def downgrade_db(revision):
    """Downgrade database to specific revision."""
    print(f"Downgrading database to revision: {revision}")
    try:
        run_alembic_command("downgrade", revision)
        print("✅ Database downgraded successfully")
    except Exception as e:
        print(f"❌ Error downgrading database: {e}")
        sys.exit(1)


def show_migrations():
    """Show migration history."""
    print("Migration history:")
    try:
        run_alembic_command("history")
    except Exception as e:
        print(f"❌ Error showing migrations: {e}")
        sys.exit(1)


def check_config():
    """Check configuration."""
    print("Checking configuration...")
    try:
        print(f"✅ Bot token: {'Set' if settings.bot_token else 'Not set'}")
        print(f"✅ Database URL: {'Set' if settings.database_url else 'Not set'}")
        print(f"✅ DeepSeek API key: {'Set' if settings.deepseek_api_key else 'Not set'}")
        print(f"✅ Payment card: {'Set' if settings.payment_card_number else 'Not set'}")
        print(f"✅ Log level: {settings.log_level}")
    except Exception as e:
        print(f"❌ Error checking configuration: {e}")
        sys.exit(1)


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python manage.py <command> [args...]")
        print("\nAvailable commands:")
        print("  init-db          - Initialize database tables")
        print("  reset-db         - Reset database (drop all tables)")
        print("  create-migration - Create new migration")
        print("  upgrade-db       - Upgrade database to latest migration")
        print("  downgrade-db     - Downgrade database to specific revision")
        print("  show-migrations  - Show migration history")
        print("  check-config     - Check configuration")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "init-db":
        asyncio.run(init_db())
    elif command == "reset-db":
        asyncio.run(reset_db())
    elif command == "create-migration":
        if len(sys.argv) < 3:
            print("Usage: python manage.py create-migration <message>")
            sys.exit(1)
        create_migration(sys.argv[2])
    elif command == "upgrade-db":
        upgrade_db()
    elif command == "downgrade-db":
        if len(sys.argv) < 3:
            print("Usage: python manage.py downgrade-db <revision>")
            sys.exit(1)
        downgrade_db(sys.argv[2])
    elif command == "show-migrations":
        show_migrations()
    elif command == "check-config":
        check_config()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main() 