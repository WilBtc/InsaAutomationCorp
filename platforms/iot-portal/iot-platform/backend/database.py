"""
Database Configuration and Session Management
==============================================
Supports both PostgreSQL (production) and SQLite (local development)
"""

import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, QueuePool

# Base class for ORM models
Base = declarative_base()

# ====================================
# DATABASE CONFIGURATION
# ====================================

# Get database URL from environment or use SQLite default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./iot_platform.db"  # Default to SQLite
)

# For PostgreSQL in production, set environment variable:
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/iot_platform

# ====================================
# ENGINE CONFIGURATION
# ====================================

# Configure engine based on database type
if DATABASE_URL.startswith("sqlite"):
    # SQLite configuration
    engine = create_async_engine(
        DATABASE_URL,
        echo=os.getenv("SQL_ECHO", "False").lower() == "true",
        connect_args={"check_same_thread": False},
        poolclass=NullPool,  # SQLite doesn't need connection pooling
    )
else:
    # PostgreSQL configuration
    engine = create_async_engine(
        DATABASE_URL,
        echo=os.getenv("SQL_ECHO", "False").lower() == "true",
        pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
        pool_pre_ping=True,  # Verify connections before using
        poolclass=QueuePool,
    )

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ====================================
# DATABASE SESSION DEPENDENCY
# ====================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database sessions in FastAPI endpoints

    Usage:
        @app.get("/items/")
        async def read_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ====================================
# DATABASE INITIALIZATION
# ====================================

async def init_db():
    """
    Initialize database tables

    For SQLite: Creates all tables automatically
    For PostgreSQL: Run migrations manually using Alembic or SQL scripts
    """
    if DATABASE_URL.startswith("sqlite"):
        # Auto-create tables for SQLite (development only)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ SQLite database initialized")
    else:
        # For PostgreSQL, tables should be created via migrations
        print("⚠️  PostgreSQL detected - ensure migrations are run")
        print("   Run: psql -U user -d iot_platform -f migrations/002_user_settings_and_sessions.sql")


async def close_db():
    """Close database connections"""
    await engine.dispose()
    print("✅ Database connections closed")


# ====================================
# HEALTH CHECK
# ====================================

async def check_db_health() -> bool:
    """
    Check if database is accessible

    Returns:
        bool: True if database is healthy, False otherwise
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"❌ Database health check failed: {e}")
        return False


# ====================================
# UTILITY FUNCTIONS
# ====================================

def get_db_type() -> str:
    """Get the current database type"""
    if DATABASE_URL.startswith("sqlite"):
        return "SQLite"
    elif DATABASE_URL.startswith("postgresql"):
        return "PostgreSQL"
    else:
        return "Unknown"


def get_db_info() -> dict:
    """Get database connection information"""
    return {
        "type": get_db_type(),
        "url": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else "local",
        "pool_size": engine.pool.size() if hasattr(engine.pool, 'size') else "N/A",
        "echo": engine.echo,
    }
