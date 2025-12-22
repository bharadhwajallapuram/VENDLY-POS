# MySQL setup
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Configure SQLite for better concurrency
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False,
        "timeout": 30,  # Wait up to 30 seconds for locks
    }

engine = create_engine(
    settings.DATABASE_URL, 
    pool_pre_ping=True, 
    future=True,
    connect_args=connect_args,
)

# Enable WAL mode for SQLite to improve concurrent access
if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=30000")  # 30 second timeout
        cursor.close()

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
