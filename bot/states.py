"""bot/states.py – FSM state groups."""
from aiogram.fsm.state import State, StatesGroup


class ChallengeCreateForm(StatesGroup):
    slug           = State()
    title_ru       = State()
    description_ru = State()
    kind           = State()
    question_ru    = State()
    schedule_time  = State()
    duration_days  = State()
    launch_at      = State()   # Step 8: immediate or specific UTC datetime


class ChallengeTranslateForm(StatesGroup):
    """Add / edit a translation for an existing challenge."""
    select_lang = State()
    title       = State()
    question    = State()


class BroadcastForm(StatesGroup):
    text = State()


class CountAnswerState(StatesGroup):
    """Active while waiting for a numeric reply to a count challenge."""
    waiting_for_count = State()
