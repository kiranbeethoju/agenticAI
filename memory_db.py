"""
SQLite Memory Database for storing LLM outputs and context
Provides persistent memory across workflow runs and sessions
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import json


class MemoryDB:
    """SQLite database for storing LLM memory/context"""

    def __init__(self, db_path: str = 'memory.db'):
        """Initialize memory database"""
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        """Get a new database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Create memory table if not exists"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                workflow_id TEXT,
                step_index INTEGER,
                step_name TEXT,
                input_text TEXT,
                output_text TEXT NOT NULL,
                provider TEXT,
                model TEXT,
                created_at TEXT NOT NULL,
                tags TEXT
            )
        ''')

        # Create indexes for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_session_id ON memory(session_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_workflow_id ON memory(workflow_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_created_at ON memory(created_at)
        ''')

        conn.commit()
        conn.close()

    def store(self, session_id: str, input_text: str, output_text: str,
             workflow_id: Optional[str] = None, step_index: Optional[int] = None,
             step_name: Optional[str] = None, provider: Optional[str] = None,
             model: Optional[str] = None, tags: Optional[List[str]] = None) -> int:
        """
        Store an LLM output to memory

        Args:
            session_id: Session identifier
            input_text: The input/prompt text
            output_text: The LLM response/output text
            workflow_id: Optional workflow identifier
            step_index: Optional step index in workflow
            step_name: Optional step name
            provider: LLM provider used (nvidia, azure_openai, gemini)
            model: Model name used
            tags: Optional list of tags for categorization

        Returns:
            int: The ID of the inserted memory entry
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        now = datetime.now().isoformat()
        tags_json = json.dumps(tags) if tags else None

        cursor.execute('''
            INSERT INTO memory (
                session_id, workflow_id, step_index, step_name,
                input_text, output_text, provider, model, created_at, tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id, workflow_id, step_index, step_name,
            input_text, output_text, provider, model, now, tags_json
        ))

        memory_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return memory_id

    def retrieve(self, session_id: str, workflow_id: Optional[str] = None,
                limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Retrieve memory entries for a session

        Args:
            session_id: Session identifier
            workflow_id: Optional filter by specific workflow
            limit: Maximum number of entries to return
            offset: Number of entries to skip

        Returns:
            List of memory entries ordered by most recent first
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        if workflow_id:
            cursor.execute('''
                SELECT * FROM memory
                WHERE session_id = ? AND workflow_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            ''', (session_id, workflow_id, limit, offset))
        else:
            cursor.execute('''
                SELECT * FROM memory
                WHERE session_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            ''', (session_id, limit, offset))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def search(self, session_id: str, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search memory entries by text content

        Args:
            session_id: Session identifier
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching memory entries
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        search_pattern = f'%{query}%'
        cursor.execute('''
            SELECT * FROM memory
            WHERE session_id = ?
            AND (input_text LIKE ? OR output_text LIKE ? OR step_name LIKE ?)
            ORDER BY created_at DESC
            LIMIT ?
        ''', (session_id, search_pattern, search_pattern, search_pattern, limit))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_recent(self, session_id: str, workflow_id: Optional[str] = None,
                 limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most recent memory entries

        Args:
            session_id: Session identifier
            workflow_id: Optional filter by specific workflow
            limit: Maximum number of entries

        Returns:
            List of most recent memory entries
        """
        return self.retrieve(session_id, workflow_id, limit, 0)

    def get_by_workflow(self, session_id: str, workflow_id: str) -> List[Dict[str, Any]]:
        """
        Get all memory entries for a specific workflow

        Args:
            session_id: Session identifier
            workflow_id: Workflow identifier

        Returns:
            List of all memory entries for the workflow
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM memory
            WHERE session_id = ? AND workflow_id = ?
            ORDER BY step_index ASC, created_at ASC
        ''', (session_id, workflow_id))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def delete_by_session(self, session_id: str) -> int:
        """
        Delete all memory entries for a session

        Args:
            session_id: Session identifier

        Returns:
            int: Number of deleted rows
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            DELETE FROM memory WHERE session_id = ?
        ''', (session_id,))

        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted_count

    def delete_by_workflow(self, session_id: str, workflow_id: str) -> int:
        """
        Delete all memory entries for a specific workflow

        Args:
            session_id: Session identifier
            workflow_id: Workflow identifier

        Returns:
            int: Number of deleted rows
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            DELETE FROM memory WHERE session_id = ? AND workflow_id = ?
        ''', (session_id, workflow_id))

        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted_count

    def get_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get memory statistics for a session

        Args:
            session_id: Session identifier

        Returns:
            Dict with memory usage statistics
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                COUNT(*) as total_entries,
                COUNT(DISTINCT workflow_id) as unique_workflows,
                SUM(LENGTH(output_text)) as total_chars
            FROM memory
            WHERE session_id = ?
        ''', (session_id,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else {'total_entries': 0, 'unique_workflows': 0, 'total_chars': 0}


# Global memory database instance
_memory_db = None


def get_memory_db() -> MemoryDB:
    """Get or create the global memory database instance"""
    global _memory_db
    if _memory_db is None:
        db_path = os.path.join(os.path.dirname(__file__), 'memory.db')
        _memory_db = MemoryDB(db_path)
    return _memory_db
