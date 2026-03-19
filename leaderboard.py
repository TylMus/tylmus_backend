import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from database import get_connection

def init_leaderboard_table():
    """Create leaderboard table if not exists."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS leaderboard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_date TEXT NOT NULL,
                user_hash TEXT NOT NULL,
                nickname TEXT NOT NULL,
                mistakes INTEGER NOT NULL,
                duration_seconds INTEGER NOT NULL DEFAULT 0,
                points INTEGER NOT NULL DEFAULT 0,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(game_date, user_hash)
            )
        """)

        # Backward-compatible migration for existing tables
        cursor = conn.execute("PRAGMA table_info(leaderboard)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        if "duration_seconds" not in existing_columns:
            conn.execute("ALTER TABLE leaderboard ADD COLUMN duration_seconds INTEGER NOT NULL DEFAULT 0")
        if "points" not in existing_columns:
            conn.execute("ALTER TABLE leaderboard ADD COLUMN points INTEGER NOT NULL DEFAULT 0")
        conn.commit()

def submit_score(
    game_date: str,
    user_hash: str,
    nickname: str,
    mistakes: int,
    duration_seconds: int,
    points: int
) -> bool:
    """
    Insert a new score. Returns True if inserted, False if already exists.
    """
    with get_connection() as conn:
        try:
            conn.execute("""
                INSERT INTO leaderboard (game_date, user_hash, nickname, mistakes, duration_seconds, points)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (game_date, user_hash, nickname, mistakes, duration_seconds, points))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Unique constraint violated – already submitted
            return False

def get_today_leaderboard(game_date: str) -> List[Dict[str, Any]]:
    """
    Retrieve today's leaderboard sorted by points (desc), then submission time (asc).
    """
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT nickname, mistakes, duration_seconds, points, submitted_at
            FROM leaderboard
            WHERE game_date = ?
            ORDER BY points DESC, submitted_at ASC
        """, (game_date,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_user_entry(game_date: str, user_hash: str) -> Optional[Dict[str, Any]]:
    """Return the user's own entry if exists."""
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT nickname, mistakes, duration_seconds, points, submitted_at
            FROM leaderboard
            WHERE game_date = ? AND user_hash = ?
        """, (game_date, user_hash))
        row = cursor.fetchone()
        return dict(row) if row else None