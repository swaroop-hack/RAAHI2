"""
Raahi Database Connection and Session Management
Supports SQLite (with optional SpatiaLite extension) and PostgreSQL / PostGIS.
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from raahi.config import settings

DATABASE_URL = os.environ.get("DATABASE_URL", settings.DATABASE_URL)

# Configure engine
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

# Attempt to load spatialite if using sqlite and available
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def load_spatialite(dbapi_conn, connection_record):
        try:
            dbapi_conn.enable_load_extension(True)
            # Try common spatialite library locations if present
            for ext in ["mod_spatialite", "spatialite", "mod_spatialite.dll", "libspatialite"]:
                try:
                    dbapi_conn.load_extension(ext)
                    break
                except Exception:
                    pass
        except Exception:
            # Fallback to pure Python Shapely geometry handling
            pass

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """FastAPI Dependency for database session management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
