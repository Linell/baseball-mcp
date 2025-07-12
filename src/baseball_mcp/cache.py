"""Lightweight on-disk cache for baseball-mcp."""

from __future__ import annotations

import json
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any
import os
import logging

import pandas as pd
from sqlalchemy import Column, DateTime, LargeBinary, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base: Any = declarative_base()


class CacheEntry(Base):
    __tablename__ = "cache"

    key = Column(String, primary_key=True)
    data = Column(LargeBinary, nullable=False)
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class Cache:
    """Tiny SQLite-backed cache storing arbitrary blobs.

    DataFrames are encoded as JSON (orient="split") before persisting.
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        """Create a cache.

        If *db_path* is None we attempt to store the database at
        ~/.config/baseball-mcp/baseball.db.  When that fails (e.g. read-only
        filesystem) we transparently fall back to an in-memory cache.
        This guarantees the server always starts even in constrained hosting platforms.
        """
        self._fallback_reason: str | None = None

        if db_path is None:
            home = Path.home()
            self.db_path = home / ".config" / "baseball-mcp" / "baseball.db"
            try:
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
            except (PermissionError, OSError) as exc:
                # Cannot create the directory – fallback to memory
                self.db_path = ":memory:"
                self._fallback_reason = f"{type(exc).__name__}: {exc}"
        else:
            self.db_path = db_path if db_path == ":memory:" else Path(db_path)

        url = "sqlite:///:memory:" if self.db_path == ":memory:" else f"sqlite:///{self.db_path}"

        # Create the SQLAlchemy engine; if the underlying SQLite file fails to
        # open (e.g. read-only parent dir) we fallback once more.
        try:
            self.engine = create_engine(url, future=True)
            Base.metadata.create_all(self.engine)
        except (OSError, PermissionError) as exc:
            # One last fallback – ensures the server keeps running.
            logging.getLogger(__name__).warning(
                "Cache: falling back to in-memory DB because opening %s failed: %s", self.db_path, exc
            )
            self.db_path = ":memory:"
            self.engine = create_engine("sqlite:///:memory:", future=True)
            Base.metadata.create_all(self.engine)
            self._fallback_reason = self._fallback_reason or f"{type(exc).__name__}: {exc}"

        if self._fallback_reason:
            logging.getLogger(__name__).info("Cache disabled (%s). Running without on-disk persistence.", self._fallback_reason)

        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)

    # Low-level helpers -----------------------------------------------------
    def _get(self, key: str) -> bytes | None:
        with self.Session() as session:
            row = session.get(CacheEntry, key)
            return bytes(row.data) if row else None

    def _set(self, key: str, blob: bytes) -> None:
        with self.Session() as session:
            entry = CacheEntry(key=key, data=blob, fetched_at=datetime.utcnow())
            session.merge(entry)
            session.commit()

    # Public helpers --------------------------------------------------------
    def get_dataframe(self, key: str) -> pd.DataFrame | None:
        raw = self._get(key)
        if raw is None:
            return None
        try:
            payload = json.loads(raw.decode("utf-8"))
            return pd.read_json(StringIO(json.dumps(payload)), orient="split")
        except Exception:
            return None

    def set_dataframe(self, key: str, df: pd.DataFrame) -> None:
        payload = df.to_json(orient="split")
        self._set(key, payload.encode("utf-8"))

    def reset(self) -> None:
        """Drop all cached data."""
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

