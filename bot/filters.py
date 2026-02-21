"""bot/filters.py – Custom aiogram filters."""
from __future__ import annotations

from aiogram.filters import Filter
from aiogram.types import Message

from bot.i18n import t, SUPPORTED_LANGS


class ButtonText(Filter):
    """
    Matches message text against ALL language translations of a button key.

    Usage:
        @router.message(ButtonText("btn_stats"))
        async def my_stats_handler(msg: Message): ...

    Works regardless of which language keyboard the user has active.
    """

    def __init__(self, *keys: str) -> None:
        self._all_texts: set[str] = set()
        for key in keys:
            for lang in SUPPORTED_LANGS:
                text = t(key, lang)
                if text and text != key:       # skip untranslated fallbacks
                    self._all_texts.add(text)

    async def __call__(self, msg: Message) -> bool:
        return bool(msg.text and msg.text in self._all_texts)
