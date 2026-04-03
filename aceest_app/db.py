import sqlite3
from contextlib import closing
from typing import Optional

from flask import current_app, g


def get_db() -> sqlite3.Connection:
    """
    Returns a request/app-scoped sqlite connection.

    Flask uses app context, so we keep one connection per context in `g`.
    """
    db = getattr(g, "db", None)
    if db is None:
        db_path = current_app.config["DB_PATH"]
        db = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
        g.db = db
    return db


def close_db() -> None:
    db = getattr(g, "db", None)
    if db is not None:
        db.close()
        g.db = None


def init_db(conn: Optional[sqlite3.Connection] = None) -> None:
    """
    Creates tables (idempotent).
    """
    if conn is None:
        conn = get_db()

    # Enable foreign keys (even if we don't heavily use them here).
    conn.execute("PRAGMA foreign_keys = ON;")

    with closing(conn.cursor()) as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                age INTEGER,
                height_cm REAL,
                weight_kg REAL,
                program TEXT,
                calories INTEGER,
                membership_end TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT NOT NULL,
                week TEXT NOT NULL,
                adherence INTEGER NOT NULL,
                UNIQUE(client_name, week),
                FOREIGN KEY(client_name) REFERENCES clients(name)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS workouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT NOT NULL,
                date TEXT NOT NULL,
                workout_type TEXT NOT NULL,
                duration_min INTEGER NOT NULL,
                notes TEXT,
                FOREIGN KEY(client_name) REFERENCES clients(name)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT NOT NULL,
                date TEXT NOT NULL,
                weight_kg REAL,
                waist_cm REAL,
                bodyfat_pct REAL,
                FOREIGN KEY(client_name) REFERENCES clients(name)
            )
            """
        )

    conn.commit()

