import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from slack_bolt import App

from community_bot.settings import Settings
from community_bot.welcome import CHANNEL_GUIDE
from community_bot.wins import wins_prompt_message

logger = logging.getLogger(__name__)


def wins_channel_id(settings: Settings) -> str:
    if settings.wins_channel:
        return settings.wins_channel
    return next(
        channel.channel_id for channel in CHANNEL_GUIDE if channel.name == "wins"
    )


def start_wins_scheduler(app: App, settings: Settings) -> BackgroundScheduler:
    channel = wins_channel_id(settings)

    def post_wins_prompt() -> None:
        logger.info("Posting weekly wins prompt to %s", channel)
        app.client.chat_postMessage(channel=channel, text=wins_prompt_message())

    scheduler = BackgroundScheduler(timezone=settings.wins_timezone)
    scheduler.add_job(
        post_wins_prompt,
        CronTrigger.from_crontab(settings.wins_cron, timezone=settings.wins_timezone),
        misfire_grace_time=3600,
    )
    scheduler.start()
    logger.info("Wins scheduler started (%s, %s)", settings.wins_cron, channel)
    return scheduler
