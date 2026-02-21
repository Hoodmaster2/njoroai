from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# SQL Schema Definitions
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    code TEXT,
    enabled BOOLEAN DEFAULT 1
);

CREATE TABLE IF NOT EXISTS state (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT,
    status TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS journal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    goal_id INTEGER,
    action TEXT,
    tool_used TEXT,
    result TEXT,
    status TEXT,
    FOREIGN KEY(goal_id) REFERENCES goals(id)
);

CREATE TABLE IF NOT EXISTS confirmations (
    action_hash TEXT PRIMARY KEY,
    goal_id INTEGER,
    action_description TEXT,
    approved BOOLEAN,
    expiry DATETIME,
    FOREIGN KEY(goal_id) REFERENCES goals(id)
);
"""

# Data Models (for application usage)
@dataclass
class Tool:
    name: str
    description: str
    code: str
    enabled: bool = True
    id: Optional[int] = None

@dataclass
class Goal:
    description: str
    status: str
    created_at: Optional[datetime] = None
    id: Optional[int] = None

@dataclass
class JournalEntry:
    goal_id: int
    action: str
    tool_used: str
    result: str
    status: str
    timestamp: Optional[datetime] = None
    id: Optional[int] = None

@dataclass
class Confirmation:
    action_hash: str
    goal_id: int
    action_description: str
    approved: bool
    expiry: datetime
