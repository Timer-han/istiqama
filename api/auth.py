"""api/auth.py – Strict Telegram WebApp initData validation.

Algorithm per https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app:
  1. Parse URL-encoded initData, extract and remove 'hash' field.
  2. Build data-check-string: remaining key=value pairs sorted alphabetically, joined by \\n.
  3. secret_key = HMAC-SHA256(key=b"WebAppData", msg=bot_token)
  4. computed   = HMAC-SHA256(key=secret_key, msg=data_check_string).hexdigest()
  5. Compare computed with received hash using constant-time compare.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Optional
from urllib.parse import parse_qsl


def verify_init_data(init_data: str, bot_token: str) -> Optional[dict]:
    """
    Validates Telegram WebApp initData string.

    Returns a dict with 'tg_user' (parsed user object) and raw 'params',
    or None if validation fails.
    """
    if not init_data or not bot_token:
        return None

    try:
        params = dict(parse_qsl(init_data, keep_blank_values=True))
    except Exception:
        return None

    received_hash = params.pop("hash", None)
    if not received_hash:
        return None

    # Build data-check-string: sorted key=value pairs joined by \n
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(params.items())
    )

    # secret_key = HMAC-SHA256(key="WebAppData", msg=bot_token)
    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    # computed = HMAC-SHA256(key=secret_key, msg=data_check_string)
    computed_hash = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        return None

    # Parse user JSON (may be absent for non-user contexts)
    user_str = params.get("user", "{}")
    try:
        tg_user = json.loads(user_str)
    except (json.JSONDecodeError, TypeError):
        tg_user = {}

    return {"tg_user": tg_user, "params": params}
