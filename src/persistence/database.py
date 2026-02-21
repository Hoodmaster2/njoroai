import sqlite3
import threading
from pathlib import Path
from contextlib import contextmanager
from src.utils.config import Config
from src.utils.logger import logger
from src.persistence.models import SCHEMA_SQL

class DatabaseManager:
    """Singleton database manager handling SQLite connections and schema initialization."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.db_path = Config.DB_PATH
        self.init_db()
        self._initialized = True
        logger.info(f"Database initialized at {self.db_path}")

    def init_db(self):
        """Initialize the database schema."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Split schema by semicolon to execute multiple statements
                statements = [s.strip() for s in SCHEMA_SQL.split(';') if s.strip()]
                for statement in statements:
                    cursor.execute(statement)
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row # Enable accessing columns by name
        try:
            yield conn
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def execute_query(self, query: str, params: tuple = ()):
        """Execute a write query safely."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid

    def fetch_all(self, query: str, params: tuple = ()):
        """Fetch all results from a query."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def fetch_one(self, query: str, params: tuple = ()):
        """Fetch a single result from a query."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()

# Global database instance
db = DatabaseManager()
