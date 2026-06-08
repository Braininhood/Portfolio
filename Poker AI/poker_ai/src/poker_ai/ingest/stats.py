"""Ingest run statistics (Phase W3)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IngestStats:
    """Result of one ingest run."""

    files_processed: int
    hands_new: int
    hands_updated: int
    hands_skipped: int

    @property
    def hands_written(self) -> int:
        """New + updated (upserts performed)."""
        return self.hands_new + self.hands_updated
