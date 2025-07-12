"""Lightweight on-disk cache for baseball-mcp."""

from __future__ import annotations

import json
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any

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
        if db_path is None:
            home = Path.home()
            self.db_path: str | Path = home / ".config" / "baseball-mcp" / "baseball.db"
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            # Allow in-memory DB via ":memory:"
            self.db_path = db_path if db_path == ":memory:" else Path(db_path)

        url = "sqlite:///:memory:" if self.db_path == ":memory:" else f"sqlite:///{self.db_path}"
        self.engine = create_engine(url, future=True)
        Base.metadata.create_all(self.engine)
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

