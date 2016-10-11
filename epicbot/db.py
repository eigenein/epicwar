#!/usr/bin/env python3
# coding: utf-8

"""
Convenient database wrapper.
"""

import datetime
import enum
import json
import sqlite3

from typing import Iterable

from epicbot.api import Building


class TaskType(enum.Enum):
    authenticate = "authenticate"
    sync = "sync"
    collect_resource = "collect_resource"
    check_alliance_help = "collect_alliance_help"
    send_gifts = "send_gifts"
    farm_gifts = "farm_gifts"


class Task:
    def __init__(self, scheduled_at: datetime.datetime, type: TaskType, arguments: dict):
        self.scheduled_at = scheduled_at
        self.type = type
        self.arguments = arguments


class Database:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def create_schema(self):
        self.connection.executescript("""
            CREATE TABLE state (
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                value TEXT,
                PRIMARY KEY (user_id, name)
            );

            CREATE TABLE tasks (
                user_id TEXT NOT NULL,          -- In-game user ID.
                scheduled_at INTEGER NOT NULL,  -- Scheduled execution timestamp.
                type TEXT NOT NULL,             -- Task type.
                arguments TEXT NOT NULL,        -- JSON-serialized task arguments (keys must be sorted).
                PRIMARY KEY (user_id, type, arguments)
            );
            CREATE INDEX ix_tasks_user_id_scheduled_at ON tasks(user_id, scheduled_at);

            CREATE TABLE buildings (
                user_id TEXT NOT NULL,
                id INTEGER NOT NULL,
                type INTEGER NOT NULL,
                level INTEGER NOT NULL,
                is_completed INTEGER NOT NULL,
                complete_timestamp INTEGER NOT NULL,
                storage_fill REAL NOT NULL,
                volume INTEGER NOT NULL,
                PRIMARY KEY (user_id, id)
            );
            CREATE INDEX ix_buildings_type ON buildings(type);
        """)

    def quick_check(self):
        """
        https://www.sqlite.org/pragma.html#pragma_quick_check
        """
        self.connection.execute("PRAGMA quick_check")

    def get_state(self, user_id: str, name: str):
        """
        Gets value of a named state variable.
        """
        row = self.connection.execute(
            "SELECT value FROM state WHERE user_id = ? AND name = ?",
            (user_id, name),
        ).fetchone()
        if row:
            return json.loads(row[0])

    def set_state(self, user_id: str, name: str, value):
        """
        Sets a value of a named state variable.
        """
        self.connection.execute(
            "INSERT OR REPLACE INTO state (user_id, name, value) VALUES (?, ?, ?)",
            (user_id, name, json.dumps(value)),
        )

    def upsert_task(self, user_id: str, task: Task, replace: bool):
        """
        Inserts or updates the task.
        """
        query = """
            INSERT OR %s INTO tasks (user_id, scheduled_at, type, arguments)
            VALUES (?, ?, ?, ?)
        """ % ("REPLACE" if replace else "IGNORE")
        with self.connection:
            self.connection.execute(query, (
                user_id,
                task.scheduled_at.timestamp(),
                task.type.value,
                json.dumps(task.arguments, sort_keys=True),
            ))

    def pick_task(self, user_id: str) -> Task:
        """
        Picks the earliest task.
        """
        row = self.connection.execute(
            "SELECT scheduled_at, type, arguments FROM tasks WHERE user_id = ? ORDER BY scheduled_at LIMIT 1",
            (user_id, ),
        ).fetchone()
        if row:
            return Task(datetime.datetime.fromtimestamp(row[0]), TaskType(row[1]), json.loads(row[2]))

    def upsert_buildings(self, user_id: str, buildings: Iterable[Building]):
        rows = [
            (user_id, building.id, building.type, building.level, building.is_completed, building.complete_time, building.storage_fill, building.volume)
            for building in buildings
        ]
        with self.connection:
            self.connection.executemany("""
                INSERT OR REPLACE INTO buildings (user_id, id, type, level, is_completed, complete_time, storage_fill, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, rows)

    def get_buildings(self, user_id: str):
        """
        Gets all buildings from the database.
        """
        rows = self.connection.execute("""
            SELECT id, type, level, is_completed, complete_time, storage_fill, volume
            FROM buildings
            WHERE user_id = ?
        """, (user_id, ))
        return [
            Building(row["id"], row["type"], row["level"], bool(row["is_completed"]), row["complete_time"], row["storage_fill"], row["volume"])
            for row in rows
        ]

    def close(self):
        self.connection.close()
