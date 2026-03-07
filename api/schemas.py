"""api/schemas.py – Pydantic request/response models."""
from __future__ import annotations

from typing import Any, List, Optional
from pydantic import BaseModel


# ── Responses ─────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: int
    display_name: str
    lang: str
    timezone: str


class ChallengeOut(BaseModel):
    id: int
    slug: str
    kind: str
    title: str
    description: str
    question: str
    options: List[str]       # non-empty only for kind='poll'
    participating: bool
    answered_today: bool
    dispatched_today: bool   # question was sent today (button active)


class StatsOut(BaseModel):
    challenge_id: int
    slug: str
    kind: str
    title: str
    stats: dict[str, Any]


class OkResponse(BaseModel):
    ok: bool
    message: str = ""


class AnswerResponse(BaseModel):
    ok: bool
    error: Optional[str] = None


# ── Requests ──────────────────────────────────────────────────────────────

class AnswerRequest(BaseModel):
    challenge_id: int
    value: Any          # "yes"/"no" | int (scale/count/poll index)


class SettingsRequest(BaseModel):
    lang: Optional[str] = None
    timezone: Optional[str] = None
