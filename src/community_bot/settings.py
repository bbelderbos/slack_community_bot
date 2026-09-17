from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="COMMUNITY_BOT_", env_file=".env")

    slack_bot_token: str
    slack_app_token: str
    database_url: str = "sqlite:///community_bot.db"
    kudos_channel: str | None = None
    save_emoji: str = "bookmark"
    wins_channel: str | None = None
    # Weekday must be a name: from_crontab reads numeric day-of-week as
    # 0=Mon..6=Sun, so "1" would mean Tuesday, not cron's Monday.
    wins_cron: str = "0 9 * * mon"
    wins_timezone: str = "UTC"
