from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.triggers.cron import CronTrigger

from community_bot.scheduler import wins_channel_id
from community_bot.settings import Settings
from community_bot.wins import WINS_PROMPTS, wins_prompt_message


def _settings(wins_channel: str | None = None) -> Settings:
    return Settings(slack_bot_token="x", slack_app_token="x", wins_channel=wins_channel)


def test_prompt_is_one_of_the_defined_prompts():
    assert wins_prompt_message() in WINS_PROMPTS


def test_every_prompt_is_non_empty():
    assert all(prompt.strip() for prompt in WINS_PROMPTS)


def test_wins_channel_prefers_explicit_setting():
    assert wins_channel_id(_settings(wins_channel="C0OVERRIDE")) == "C0OVERRIDE"


def test_wins_channel_falls_back_to_channel_guide():
    assert wins_channel_id(_settings()) == "C000WINS"


def test_default_schedule_fires_monday_at_nine():
    settings = _settings()
    tz = ZoneInfo(settings.wins_timezone)
    trigger = CronTrigger.from_crontab(settings.wins_cron, timezone=tz)
    # from a Sunday, the next fire must be the following Monday at 09:00
    sunday = datetime(2026, 9, 6, 12, 0, tzinfo=tz)
    fire = trigger.get_next_fire_time(None, sunday)
    assert fire.weekday() == 0  # Monday
    assert (fire.hour, fire.minute) == (9, 0)
