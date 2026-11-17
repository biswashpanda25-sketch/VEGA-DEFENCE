from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import get_settings

settings = get_settings()
connect_args: dict = {}
if settings.DATABASE_URL.startswith("postgresql"):
    # PostgreSQL tuning, applied at connection establishment so it cannot be rolled back.
    #
    # `jit=off`: measured during the 1M-row benchmark, JIT compilation added ~180 ms of fixed
    #   latency to interactive queries (a 1-2 ms spatial KNN query became 181 ms, of which 181.8 ms
    #   was JIT optimisation). Long-running analytics lose little; interactive latency is the SLO.
    # `statement_timeout`: a safety net so a pathological query cannot pin a worker indefinitely.
    connect_args = {"options": "-c jit=off -c statement_timeout=60000"}
elif settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
