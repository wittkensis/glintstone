#!/usr/bin/env python3
"""
Checkpoint/resume infrastructure for citation import scripts.

Provides atomic state persistence, graceful signal handling,
and progress reporting. Pattern extracted from import_cdli_catalog.py.
"""

import hashlib
import json
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

PROGRESS_DIR = Path(__file__).parent.parent / "_progress"


class ImportCheckpoint:
    """Manages checkpoint state for resumable imports."""

    def __init__(self, name: str, reset: bool = False):
        """
        Args:
            name: Identifier for this import (e.g., "cdli_publications")
            reset: If True, discard existing checkpoint and start fresh
        """
        self.name = name
        self.checkpoint_path = PROGRESS_DIR / f"{name}_state.json"
        self.interrupted = False
        self.state = self._fresh_state() if reset else self._load_state()
        self.stats = self.state.get("stats", self._fresh_stats())

        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)

    def _handle_interrupt(self, signum, frame):
        print("\n\n  Interrupt received. Saving checkpoint...")
        self.interrupted = True

    def _fresh_state(self) -> dict:
        return {
            "last_offset": 0,
            "source_checksum": None,
            "started_at": datetime.now().isoformat(),
            "completed": False,
            "total_items": 0,
            "stats": self._fresh_stats(),
        }

    def _fresh_stats(self) -> dict:
        return {
            "processed": 0,
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "errors": [],
        }

    def _load_state(self) -> dict:
        if self.checkpoint_path.exists():
            try:
                with open(self.checkpoint_path) as f:
                    state = json.load(f)
                    # Restore stats from checkpoint
                    if "stats" in state:
                        return state
            except (json.JSONDecodeError, IOError):
                pass
        return self._fresh_state()

    def save(self, completed: bool = False):
        """Atomically save checkpoint state."""
        self.state["last_offset"] = self.stats["processed"]
        self.state["completed"] = completed
        self.state["last_updated"] = datetime.now().isoformat()
        self.state["stats"] = self.stats.copy()
        # Trim errors to last 20
        self.state["stats"]["errors"] = self.stats["errors"][-20:]

        PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
        temp = self.checkpoint_path.with_suffix(".tmp")
        with open(temp, "w") as f:
            json.dump(self.state, f, indent=2)
        temp.rename(self.checkpoint_path)

    def is_completed(self, source_checksum: Optional[str] = None) -> bool:
        """Check if import already completed for this source data."""
        if not self.state.get("completed"):
            return False
        if source_checksum and self.state.get("source_checksum") != source_checksum:
            return False
        return True

    @property
    def resume_offset(self) -> int:
        """Row/page to resume from."""
        return self.state.get("last_offset", 0)

    def set_source_checksum(self, checksum: str):
        self.state["source_checksum"] = checksum

    def set_total(self, total: int):
        self.state["total_items"] = total

    def record_error(self, item_id: str, error: str):
        self.stats["errors"].append({
            "item": item_id,
            "error": str(error),
            "at": datetime.now().isoformat(),
        })

    def print_progress(self, current: int, total: Optional[int] = None):
        total = total or self.state.get("total_items", 0)
        if total > 0:
            pct = (current / total) * 100
            print(f"    Progress: {current:,} / {total:,} ({pct:.1f}%)", end="\r")
        else:
            print(f"    Progress: {current:,}", end="\r")

    def print_summary(self):
        print(f"\n{'=' * 60}")
        print(f"  {self.name.upper()} SUMMARY")
        print(f"{'=' * 60}")
        print(f"  Processed: {self.stats['processed']:,}")
        print(f"  Inserted:  {self.stats['inserted']:,}")
        print(f"  Updated:   {self.stats['updated']:,}")
        print(f"  Skipped:   {self.stats['skipped']:,}")

        if self.stats["errors"]:
            print(f"\n  Errors ({len(self.stats['errors'])}):")
            for err in self.stats["errors"][:5]:
                print(f"    {err['item']}: {err['error']}")
            if len(self.stats["errors"]) > 5:
                print(f"    ... and {len(self.stats['errors']) - 5} more")


def compute_file_checksum(path: Path) -> str:
    """Quick checksum of first 10KB for file identity."""
    with open(path, "rb") as f:
        return hashlib.sha256(f.read(10240)).hexdigest()[:16]
