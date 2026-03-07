"""api/main.py – FastAPI application: REST API + static file serving."""
from __future__ import annotations

import logging
import os
from datetime import date
from pathlib import Path
from typing import List

import pytz
from asyncpg import Record
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import services.db as db
from adapters.storage_postgres import fetch, init_pool
from api.deps import get_current_user
from api.schemas import (
    AnswerRequest,
    AnswerResponse,
    ChallengeOut,
    OkResponse,
    SettingsRequest,
    StatsOut,
    UserResponse,
)
from bot.i18n import KIND_LABELS, SUPPORTED_LANGS, t
from bot.utils import challenge_description, challenge_options, challenge_text

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent.parent / "static"

app = FastAPI(title="Istiqama Mini App API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup() -> None:
    dsn = os.getenv(
        "DATABASE_URL", "postgresql://istiqama:istiqama@db:5432/istiqama"
    )
    await init_pool(dsn)
    logger.info("API: DB pool initialised")


# ── Static files ───────────────────────────────────────────────────────────

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
async def serve_webapp() -> FileResponse:
    html = STATIC_DIR / "app.html"
    if not html.exists():
        raise HTTPException(status_code=404, detail="app.html not found")
    return FileResponse(str(html), media_type="text/html")


# ── /api/me ────────────────────────────────────────────────────────────────

@app.get("/api/me", response_model=UserResponse)
async def get_me(user: Record = Depends(get_current_user)) -> dict:
    return {
        "id": user["id"],
        "display_name": user["display_name"] or "User",
        "lang": user["lang"] or "ru",
        "timezone": user["timezone"] or "UTC",
    }


# ── /api/i18n ──────────────────────────────────────────────────────────────

_WEBAPP_I18N_KEYS = [
    "webapp_greeting", "webapp_subtitle", "webapp_loading", "webapp_error_load",
    "webapp_no_participation", "webapp_btn_answer", "webapp_btn_done", "webapp_btn_wait",
    "webapp_btn_join", "webapp_btn_leave", "webapp_no_challenges_list",
    "webapp_btn_location", "webapp_lang_header", "webapp_tz_label",
    "webapp_btn_submit", "webapp_already_answered",
    "webapp_nav_today", "webapp_nav_stats", "webapp_nav_challenges", "webapp_nav_settings",
    "webapp_header_stats", "webapp_header_challenges", "webapp_header_settings",
    "webapp_no_stats", "webapp_no_answers_yet",
    "webapp_stat_yes_pct", "webapp_stat_days", "webapp_stat_streak", "webapp_stat_record",
    "webapp_stat_avg7", "webapp_stat_avg_all", "webapp_stat_max",
    # Reuse existing bot keys
    "btn_yes", "btn_no",
]


@app.get("/api/i18n")
async def get_i18n(user: Record = Depends(get_current_user)) -> dict:
    """
    Returns all UI strings translated into the user's language.
    The frontend uses this as its single source of truth for all text.
    Falls back to 'ru' for any missing translation, matching bot behaviour.
    """
    lang = user["lang"] or "ru"
    result: dict = {key: t(key, lang) for key in _WEBAPP_I18N_KEYS}
    # Challenge kind labels (kind_yes_no, kind_count, kind_scale_1_5, kind_poll)
    for kind, labels in KIND_LABELS.items():
        result[f"kind_{kind}"] = labels.get(lang) or labels.get("ru", kind)
    return result


# ── /api/challenges ────────────────────────────────────────────────────────

@app.get("/api/challenges", response_model=List[ChallengeOut])
async def get_challenges(user: Record = Depends(get_current_user)) -> list:
    lang = user["lang"] or "ru"
    tz_str = user["timezone"] or "UTC"
    today: date = db.local_day_for_tz(tz_str)

    rows = await fetch(
        """
        SELECT
            c.id, c.slug, c.kind, c.metadata, c.active,
            cp.active           AS participating,
            cp.last_dispatch_day,
            cp.last_answer_day
        FROM challenges c
        LEFT JOIN challenge_participants cp
               ON cp.challenge_id = c.id AND cp.user_id = $1
        WHERE c.active = TRUE
        ORDER BY c.id
        """,
        user["id"],
    )

    result = []
    for c in rows:
        title, question = challenge_text(c, lang)
        desc = challenge_description(c, lang)
        opts = challenge_options(c, lang) if c["kind"] == "poll" else []
        participating = bool(c["participating"])
        answered = bool(c["last_answer_day"] and c["last_answer_day"] == today)
        dispatched = bool(c["last_dispatch_day"] and c["last_dispatch_day"] == today)
        result.append({
            "id": c["id"], "slug": c["slug"], "kind": c["kind"],
            "title": title, "description": desc, "question": question,
            "options": opts, "participating": participating,
            "answered_today": answered, "dispatched_today": dispatched,
        })
    return result


# ── /api/challenges/{id}/join  &  leave ───────────────────────────────────

@app.post("/api/challenges/{challenge_id}/join", response_model=OkResponse)
async def join_challenge(challenge_id: int, user: Record = Depends(get_current_user)) -> dict:
    joined = await db.join_challenge(user["id"], challenge_id, user["timezone"] or "UTC")
    return {"ok": True, "message": "joined" if joined else "already_participating"}


@app.post("/api/challenges/{challenge_id}/leave", response_model=OkResponse)
async def leave_challenge(challenge_id: int, user: Record = Depends(get_current_user)) -> dict:
    await db.leave_challenge(user["id"], challenge_id)
    return {"ok": True, "message": "left"}


# ── /api/stats ─────────────────────────────────────────────────────────────

@app.get("/api/stats", response_model=List[StatsOut])
async def get_stats(user: Record = Depends(get_current_user)) -> list:
    lang = user["lang"] or "ru"
    participations = await db.get_active_participations_for_user(user["id"])
    result = []
    for p in participations:
        raw_stats = await db.get_user_challenge_stats(user["id"], p["challenge_id"])
        title, _ = challenge_text(p, lang)
        result.append({
            "challenge_id": p["challenge_id"],
            "slug": p["slug"],
            "kind": p["kind"],
            "title": title,
            "stats": _sanitise(raw_stats),
        })
    return result


def _sanitise(obj):
    """Recursively convert asyncpg Records and dates to JSON-safe types."""
    if isinstance(obj, dict):
        return {k: _sanitise(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitise(i) for i in obj]
    if isinstance(obj, date):
        return obj.isoformat()
    # asyncpg Record — итерируем через .keys(), не через dict()
    # dict(record) падает с ValueError, потому что Record итерируется как значения, не пары
    try:
        keys = obj.keys()
        return {k: _sanitise(obj[k]) for k in keys}
    except (AttributeError, TypeError):
        pass
    return obj


# ── /api/answer ────────────────────────────────────────────────────────────

@app.post("/api/answer", response_model=AnswerResponse)
async def post_answer(body: AnswerRequest, user: Record = Depends(get_current_user)) -> dict:
    challenge = await db.get_challenge_by_id(body.challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    value = body.value
    if challenge["kind"] in ("count", "scale_1_5", "poll"):
        try:
            value = int(value)
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail="value must be an integer")
    elif challenge["kind"] == "yes_no":
        value = str(value).lower()
        if value not in ("yes", "no"):
            raise HTTPException(status_code=422, detail="value must be 'yes' or 'no'")

    event = await db.record_event(
        user_id=user["id"], challenge_id=body.challenge_id,
        tz_str=user["timezone"] or "UTC", payload={"value": value},
    )
    if event is None:
        return {"ok": False, "error": "already_answered"}

    try:
        today = db.local_day_for_tz(user["timezone"] or "UTC")
        await db.mark_queue_answered(user["id"], body.challenge_id, today)
    except Exception:
        pass
    return {"ok": True}


# ── /api/settings ──────────────────────────────────────────────────────────

@app.post("/api/settings", response_model=OkResponse)
async def update_settings(body: SettingsRequest, user: Record = Depends(get_current_user)) -> dict:
    if body.lang is not None:
        if body.lang not in SUPPORTED_LANGS:
            raise HTTPException(status_code=422, detail=f"Unsupported lang: {body.lang}")
        await db.update_user_lang(user["id"], body.lang)

    if body.timezone is not None:
        try:
            pytz.timezone(body.timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            raise HTTPException(status_code=422, detail=f"Unknown timezone: {body.timezone}")
        await db.update_user_timezone(user["id"], body.timezone)
        await db.refresh_dispatch_times_for_user(user["id"], body.timezone)

    return {"ok": True, "message": "updated"}