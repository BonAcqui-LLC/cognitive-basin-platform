"""
SQLite-backed BasinLab session persistence.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
import uuid
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


SCHEMA_VERSION = 1


class SessionStoreError(RuntimeError):
    pass


class SessionCorruptionError(SessionStoreError):
    pass


class SessionSchemaMismatchError(SessionStoreError):
    pass


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass
class StoredSession:
    session_id: str
    created_at: float
    updated_at: float
    metadata: Dict[str, Any]
    final_basin: Dict[str, Any]
    latest_event_id: str
    latest_snapshot_hash: str
    schema_version: int


class SessionStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / "basinlab.sqlite3"
        self.exports_dir = self.root / "exports"
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = FULL")
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    metadata_json TEXT NOT NULL,
                    final_basin_json TEXT NOT NULL,
                    latest_event_id TEXT NOT NULL DEFAULT '',
                    latest_snapshot_hash TEXT NOT NULL DEFAULT '',
                    schema_version INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                    session_id TEXT NOT NULL,
                    seq INTEGER NOT NULL,
                    event_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    parent_event_id TEXT NOT NULL DEFAULT '',
                    timestamp REAL NOT NULL,
                    payload_json TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    PRIMARY KEY (session_id, seq),
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS snapshots (
                    session_id TEXT NOT NULL,
                    seq INTEGER NOT NULL,
                    event_id TEXT NOT NULL,
                    snapshot_json TEXT NOT NULL,
                    snapshot_hash TEXT NOT NULL,
                    PRIMARY KEY (session_id, seq),
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS artifacts (
                    session_id TEXT NOT NULL,
                    artifact_id TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    artifact_path TEXT NOT NULL,
                    artifact_hash TEXT NOT NULL,
                    exists_on_disk INTEGER NOT NULL,
                    temporary INTEGER NOT NULL,
                    pruned INTEGER NOT NULL DEFAULT 0,
                    metadata_json TEXT NOT NULL,
                    PRIMARY KEY (session_id, artifact_id),
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS replay_hashes (
                    session_id TEXT NOT NULL,
                    replay_hash TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    result_json TEXT NOT NULL,
                    PRIMARY KEY (session_id, replay_hash),
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                );
                """
            )
            current_version = connection.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()
            if current_version is None:
                connection.execute(
                    "INSERT INTO meta(key, value) VALUES ('schema_version', ?)", (str(SCHEMA_VERSION),)
                )
            elif int(current_version["value"]) != SCHEMA_VERSION:
                raise SessionSchemaMismatchError(
                    f"Unsupported BasinLab session schema version: {current_version['value']}"
                )
            connection.commit()

    def create_session(self, metadata: Dict[str, Any], session_id: Optional[str] = None) -> str:
        created_at = time.time()
        identifier = session_id or f"bls-{uuid.uuid4().hex[:12]}"
        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT INTO sessions(
                    session_id, created_at, updated_at, metadata_json, final_basin_json,
                    latest_event_id, latest_snapshot_hash, schema_version
                ) VALUES (?, ?, ?, ?, ?, '', '', ?)
                """,
                (
                    identifier,
                    created_at,
                    created_at,
                    _canonical_json(metadata),
                    _canonical_json({}),
                    SCHEMA_VERSION,
                ),
            )
            connection.commit()
        return identifier

    def session_exists(self, session_id: str) -> bool:
        with closing(self._connect()) as connection:
            row = connection.execute("SELECT 1 FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
        return row is not None

    def append_event(
        self,
        session_id: str,
        event: Dict[str, Any],
        *,
        snapshot: Optional[Dict[str, Dict[str, Any]]] = None,
        final_basin: Optional[Dict[str, Any]] = None,
        simulate_interrupt: bool = False,
    ) -> None:
        payload_json = _canonical_json(event)
        payload_hash = _sha256_text(payload_json)
        with closing(self._connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    "SELECT COALESCE(MAX(seq), 0) AS max_seq FROM events WHERE session_id = ?",
                    (session_id,),
                ).fetchone()
                next_seq = int(row["max_seq"]) + 1
                connection.execute(
                    """
                    INSERT INTO events(
                        session_id, seq, event_id, event_type, parent_event_id,
                        timestamp, payload_json, payload_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        next_seq,
                        event.get("event_id", f"event-{next_seq:04d}"),
                        event.get("type", "event"),
                        event.get("parent_event_id", "") or "",
                        float(event.get("timestamp", time.time())),
                        payload_json,
                        payload_hash,
                    ),
                )
                latest_snapshot_hash = ""
                if snapshot is not None:
                    snapshot_json = _canonical_json(snapshot)
                    latest_snapshot_hash = _sha256_text(snapshot_json)
                    connection.execute(
                        """
                        INSERT INTO snapshots(session_id, seq, event_id, snapshot_json, snapshot_hash)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            session_id,
                            next_seq,
                            event.get("event_id", f"event-{next_seq:04d}"),
                            snapshot_json,
                            latest_snapshot_hash,
                        ),
                    )
                if simulate_interrupt:
                    raise SessionStoreError("Simulated interrupted write")
                connection.execute(
                    """
                    UPDATE sessions
                    SET updated_at = ?, latest_event_id = ?, latest_snapshot_hash = COALESCE(NULLIF(?, ''), latest_snapshot_hash),
                        final_basin_json = COALESCE(NULLIF(?, ''), final_basin_json)
                    WHERE session_id = ?
                    """,
                    (
                        time.time(),
                        event.get("event_id", ""),
                        latest_snapshot_hash,
                        _canonical_json(final_basin) if final_basin is not None else "",
                        session_id,
                    ),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    def register_artifact(
        self,
        session_id: str,
        path: str | Path,
        *,
        event_id: str = "",
        artifact_type: str = "artifact",
        temporary: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        artifact_path = Path(path)
        exists_on_disk = artifact_path.exists()
        payload = {
            "artifact_type": artifact_type,
            "size_bytes": artifact_path.stat().st_size if exists_on_disk else 0,
            **(metadata or {}),
        }
        artifact_hash = _sha256_file(artifact_path) if exists_on_disk and artifact_path.is_file() else ""
        artifact_id = _sha256_text(f"{session_id}:{event_id}:{artifact_path}")
        record = {
            "artifact_id": artifact_id,
            "artifact_path": str(artifact_path),
            "artifact_hash": artifact_hash,
            "exists_on_disk": exists_on_disk,
            "temporary": temporary,
            "pruned": False,
            "metadata": payload,
        }
        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO artifacts(
                    session_id, artifact_id, event_id, artifact_path, artifact_hash,
                    exists_on_disk, temporary, pruned, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    artifact_id,
                    event_id,
                    str(artifact_path),
                    artifact_hash,
                    1 if exists_on_disk else 0,
                    1 if temporary else 0,
                    0,
                    _canonical_json(payload),
                ),
            )
            connection.commit()
        return record

    def prune_temporary_artifacts(self, session_id: str) -> List[str]:
        pruned: List[str] = []
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT artifact_id, artifact_path
                FROM artifacts
                WHERE session_id = ? AND temporary = 1 AND pruned = 0
                """,
                (session_id,),
            ).fetchall()
            for row in rows:
                artifact_path = Path(row["artifact_path"])
                if artifact_path.exists() and artifact_path.is_file():
                    artifact_path.unlink()
                connection.execute(
                    """
                    UPDATE artifacts
                    SET exists_on_disk = 0, pruned = 1
                    WHERE session_id = ? AND artifact_id = ?
                    """,
                    (session_id, row["artifact_id"]),
                )
                pruned.append(str(artifact_path))
            connection.commit()
        return pruned

    def get_session(self, session_id: str) -> StoredSession:
        with closing(self._connect()) as connection:
            row = connection.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
        if row is None:
            raise SessionStoreError(f"Unknown session ID: {session_id}")
        if int(row["schema_version"]) != SCHEMA_VERSION:
            raise SessionSchemaMismatchError(
                f"Session {session_id} uses schema {row['schema_version']}, expected {SCHEMA_VERSION}"
            )
        return StoredSession(
            session_id=row["session_id"],
            created_at=float(row["created_at"]),
            updated_at=float(row["updated_at"]),
            metadata=json.loads(row["metadata_json"]),
            final_basin=json.loads(row["final_basin_json"]),
            latest_event_id=row["latest_event_id"],
            latest_snapshot_hash=row["latest_snapshot_hash"],
            schema_version=int(row["schema_version"]),
        )

    def list_sessions(self) -> List[StoredSession]:
        sessions: List[StoredSession] = []
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT * FROM sessions ORDER BY updated_at DESC, created_at DESC, session_id ASC"
            ).fetchall()
        for row in rows:
            if int(row["schema_version"]) != SCHEMA_VERSION:
                raise SessionSchemaMismatchError(
                    f"Session {row['session_id']} uses schema {row['schema_version']}, expected {SCHEMA_VERSION}"
                )
            sessions.append(
                StoredSession(
                    session_id=row["session_id"],
                    created_at=float(row["created_at"]),
                    updated_at=float(row["updated_at"]),
                    metadata=json.loads(row["metadata_json"]),
                    final_basin=json.loads(row["final_basin_json"]),
                    latest_event_id=row["latest_event_id"],
                    latest_snapshot_hash=row["latest_snapshot_hash"],
                    schema_version=int(row["schema_version"]),
                )
            )
        return sessions

    def read_events(self, session_id: str) -> List[Dict[str, Any]]:
        self.get_session(session_id)
        events: List[Dict[str, Any]] = []
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT payload_json, payload_hash FROM events WHERE session_id = ? ORDER BY seq ASC",
                (session_id,),
            ).fetchall()
        for row in rows:
            payload_json = row["payload_json"]
            if _sha256_text(payload_json) != row["payload_hash"]:
                raise SessionCorruptionError(f"Corrupt event record detected for session {session_id}")
            events.append(json.loads(payload_json))
        return events

    def latest_snapshot(self, session_id: str) -> Dict[str, Any]:
        self.get_session(session_id)
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT snapshot_json, snapshot_hash FROM snapshots WHERE session_id = ? ORDER BY seq DESC LIMIT 1",
                (session_id,),
            ).fetchone()
        if row is None:
            return {"snapshot": {}, "snapshot_hash": ""}
        snapshot_json = row["snapshot_json"]
        if _sha256_text(snapshot_json) != row["snapshot_hash"]:
            raise SessionCorruptionError(f"Corrupt snapshot record detected for session {session_id}")
        return {"snapshot": json.loads(snapshot_json), "snapshot_hash": row["snapshot_hash"]}

    def list_snapshots(self, session_id: str) -> List[Dict[str, Any]]:
        self.get_session(session_id)
        snapshots: List[Dict[str, Any]] = []
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT seq, event_id, snapshot_json, snapshot_hash
                FROM snapshots
                WHERE session_id = ?
                ORDER BY seq ASC
                """,
                (session_id,),
            ).fetchall()
        for row in rows:
            snapshot_json = row["snapshot_json"]
            if _sha256_text(snapshot_json) != row["snapshot_hash"]:
                raise SessionCorruptionError(f"Corrupt snapshot record detected for session {session_id}")
            snapshots.append(
                {
                    "seq": int(row["seq"]),
                    "event_id": row["event_id"],
                    "snapshot": json.loads(snapshot_json),
                    "snapshot_hash": row["snapshot_hash"],
                }
            )
        return snapshots

    def list_artifacts(self, session_id: str) -> List[Dict[str, Any]]:
        self.get_session(session_id)
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT artifact_id, artifact_path, artifact_hash, exists_on_disk, temporary, pruned, metadata_json
                FROM artifacts
                WHERE session_id = ?
                ORDER BY artifact_path
                """,
                (session_id,),
            ).fetchall()
        artifacts = []
        for row in rows:
            path = Path(row["artifact_path"])
            artifacts.append(
                {
                    "artifact_id": row["artifact_id"],
                    "artifact_path": row["artifact_path"],
                    "artifact_hash": row["artifact_hash"],
                    "exists_on_disk": bool(row["exists_on_disk"]) and path.exists(),
                    "temporary": bool(row["temporary"]),
                    "pruned": bool(row["pruned"]),
                    "metadata": json.loads(row["metadata_json"]),
                }
            )
        return artifacts

    def record_replay_hash(self, session_id: str, replay_result: Dict[str, Any]) -> str:
        payload_json = _canonical_json(replay_result)
        replay_hash = _sha256_text(payload_json)
        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO replay_hashes(session_id, replay_hash, created_at, result_json)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, replay_hash, time.time(), payload_json),
            )
            connection.commit()
        return replay_hash

    def inspect_session(self, session_id: str) -> Dict[str, Any]:
        session = self.get_session(session_id)
        events = self.read_events(session_id)
        artifacts = self.list_artifacts(session_id)
        issues = []
        for artifact in artifacts:
            if not artifact["exists_on_disk"] and not artifact["pruned"]:
                issues.append(f"Missing artifact: {artifact['artifact_path']}")
        return {
            "session_id": session.session_id,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "metadata": session.metadata,
            "final_basin": session.final_basin,
            "latest_event_id": session.latest_event_id,
            "latest_snapshot_hash": session.latest_snapshot_hash,
            "event_count": len(events),
            "artifacts": artifacts,
            "issues": issues,
            "schema_version": session.schema_version,
        }

    def diff_sessions(self, left_session_id: str, right_session_id: str) -> Dict[str, Any]:
        left = self.inspect_session(left_session_id)
        right = self.inspect_session(right_session_id)
        return {
            "left_session_id": left_session_id,
            "right_session_id": right_session_id,
            "event_count_delta": left["event_count"] - right["event_count"],
            "left_final_basin": left["final_basin"],
            "right_final_basin": right["final_basin"],
            "metadata_delta": {
                key: [left["metadata"].get(key), right["metadata"].get(key)]
                for key in sorted(set(left["metadata"]) | set(right["metadata"]))
                if left["metadata"].get(key) != right["metadata"].get(key)
            },
            "issue_count_delta": len(left["issues"]) - len(right["issues"]),
        }

    def export_portable_session(self, session_id: str, output_path: str | Path) -> Dict[str, Any]:
        export_payload = {
            "session": self.inspect_session(session_id),
            "events": self.read_events(session_id),
            "snapshot": self.latest_snapshot(session_id),
            "artifacts": self.list_artifacts(session_id),
        }
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(export_payload, indent=2, sort_keys=True), encoding="utf-8")
        return {
            "path": str(destination),
            "sha256": _sha256_file(destination),
            "size_bytes": destination.stat().st_size,
        }

    def tamper_event_for_test(self, session_id: str, seq: int, payload: Dict[str, Any]) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                "UPDATE events SET payload_json = ? WHERE session_id = ? AND seq = ?",
                (_canonical_json(payload), session_id, seq),
            )
            connection.commit()

    def set_schema_version_for_test(self, version: int) -> None:
        with closing(self._connect()) as connection:
            connection.execute("UPDATE meta SET value = ? WHERE key = 'schema_version'", (str(version),))
            connection.commit()
