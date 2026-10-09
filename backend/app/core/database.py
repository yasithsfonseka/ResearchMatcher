from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    # Have Postgres abort stuck statements (30s) and idle-in-transaction sessions (60s)
    # so an abandoned request cannot hold row locks indefinitely.
    connect_args={
        "options": "-c statement_timeout=30000 -c idle_in_transaction_session_timeout=60000"
    }
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base model
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
