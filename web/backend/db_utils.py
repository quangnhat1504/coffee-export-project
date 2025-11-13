"""
Database utility functions for connection management and query execution
"""
from typing import Optional, Dict, Any, Tuple
from sqlalchemy import create_engine, Engine, text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError
import os
import tempfile
from contextlib import contextmanager


def create_database_engine(
    host: str,
    user: str,
    password: str,
    port: str = "3306",
    database: str = "defaultdb",
    ca_cert: Optional[str] = None
) -> Engine:
    """
    Create database engine with robust fallback strategies.
    
    Args:
        host: Database host
        user: Database user
        password: Database password
        port: Database port
        database: Database name
        ca_cert: SSL certificate content (optional)
    
    Returns:
        SQLAlchemy Engine
    
    Raises:
        Exception: If all connection strategies fail
    """
    base_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    
    # Strategy 1: Try without SSL (most reliable for Aiven)
    try:
        engine = create_engine(
            base_url,
            connect_args={
                "ssl": False,
                "connect_timeout": 10,
                "read_timeout": 30,
                "write_timeout": 30
            },
            pool_pre_ping=True,
            pool_recycle=1800,
            pool_size=10,
            max_overflow=20,
            echo=False
        )
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception:
        pass
    
    # Strategy 2: Try with SSL if certificate available
    if ca_cert and ca_cert.strip():
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pem') as f:
                f.write(ca_cert)
                cert_file = f.name
            
            engine = create_engine(
                base_url,
                connect_args={
                    "ssl": {"ca": cert_file},
                    "connect_timeout": 30
                },
                pool_pre_ping=True,
                pool_recycle=3600,
                pool_size=5,
                max_overflow=10,
                echo=False
            )
            # Test connection
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            return engine
        except Exception:
            pass
    
    # Strategy 3: Try with default SSL mode
    try:
        engine = create_engine(
            base_url,
            connect_args={"connect_timeout": 30},
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=5,
            max_overflow=10,
            echo=False
        )
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception:
        pass
    
    # All strategies failed
    raise Exception(
        "Unable to connect to database after trying all strategies. "
        "Please check your credentials and network connection."
    )


@contextmanager
def get_db_connection(engine: Engine):
    """
    Context manager for database connections.
    
    Args:
        engine: SQLAlchemy Engine
    
    Yields:
        Database Connection
    """
    conn = engine.connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def check_connection(engine: Optional[Engine]) -> Tuple[bool, str]:
    """
    Check if database connection is available.
    
    Args:
        engine: SQLAlchemy Engine (can be None)
    
    Returns:
        Tuple of (is_connected, message)
    """
    if engine is None:
        return False, "Database engine not initialized"
    
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "Database connected"
    except Exception as e:
        return False, f"Database connection error: {str(e)}"

