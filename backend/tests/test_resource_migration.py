import os
from pathlib import Path
import sqlite3
import subprocess
import sys


def test_resource_migration_consolidates_duplicates_and_roundtrips(tmp_path):
    database = tmp_path / "migration.db"
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{database}"}
    backend = Path(__file__).resolve().parents[1]
    def migrate(*args):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *args], cwd=backend, env=env,
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, result.stderr
    migrate("upgrade", "c2d3e4f5a6b7")
    with sqlite3.connect(database) as connection:
        for _ in range(2):
            connection.execute("""
                INSERT INTO processing_jobs (category, job_type, target_id, title, status, created_at)
                VALUES ('ai', 'ai_document_summary', '1', 'Relatório fictício', 'pending', '2026-01-01')
            """)
    migrate("upgrade", "head")
    with sqlite3.connect(database) as connection:
        statuses = connection.execute("SELECT status FROM processing_jobs ORDER BY id").fetchall()
        assert statuses == [("pending",), ("cancelled",)]
        assert "execution_token" in {row[1] for row in connection.execute("PRAGMA table_info(processing_jobs)")}
        assert connection.execute("SELECT COUNT(*) FROM resource_leases").fetchone() == (0,)
    migrate("downgrade", "c2d3e4f5a6b7")
    migrate("upgrade", "head")
