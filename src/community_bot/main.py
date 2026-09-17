import logging

from slack_bolt.adapter.socket_mode import SocketModeHandler

from community_bot.app import create_app
from community_bot.scheduler import start_wins_scheduler
from community_bot.settings import Settings


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = Settings()  # type: ignore[call-arg]

    app = create_app(settings)
    start_wins_scheduler(app, settings)
    SocketModeHandler(app, settings.slack_app_token).start()


if __name__ == "__main__":
    main()
