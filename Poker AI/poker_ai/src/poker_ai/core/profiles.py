"""Pydantic models for player / bot profiles (Phase 2)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PlayerProfile(BaseModel):
    """Lightweight profile used by policies and simulators."""

    model_config = ConfigDict(frozen=True)

    profile_id: str = Field(min_length=1, description="Stable id for this profile.")
    display_name: str = Field(default="Player", min_length=1)
    notes: str | None = None
