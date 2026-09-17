import logging

from slack_bolt import App

from community_bot.db import create_session_factory
from community_bot.kudos import KUDOS_PATTERN, kudos_message, parse_kudos, record_kudos
from community_bot.saved import (
    already_saved,
    delete_saved_message,
    forget_author,
    format_search_results,
    save_message,
    search_saved,
)
from community_bot.settings import Settings
from community_bot.slack import fetch_message
from community_bot.welcome import format_channel_guide, welcome_message

logger = logging.getLogger(__name__)

HELP_KEYWORDS = frozenset({"help", "hi", "hello", "commands"})
SEARCH_PREFIX = "search "
FORGET_KEYWORD = "forget me"

HELP_MSG = """Here's what I do:

• I welcome new members with a DM when they join.
• Write `@someone ++` and I'll pass on the kudos in the channel.
• React :{save_emoji}: on any message and I'll save it to the community archive \
— text and all, so it survives Slack's 90-day limit.
• DM me `search <term>` to dig the archive back up.
• DM me `forget me` and I'll drop everything you posted from the archive.

*The channels*
{channel_guide}

Anything else, just ask an admin.
"""


def create_app(settings: Settings) -> App:
    app = App(token=settings.slack_bot_token)
    session_factory = create_session_factory(settings.database_url)
    bot_id = app.client.auth_test()["user_id"]

    @app.event("team_join")
    def welcome_new_member(event, client):
        user_id = event["user"]["id"]
        logger.info("Welcoming new member %s", user_id)
        client.chat_postMessage(channel=user_id, text=welcome_message(user_id))

    @app.message(KUDOS_PATTERN)
    def handle_kudos(message, client):
        if message.get("bot_id"):
            return

        giver_id = message["user"]
        channel_id = message["channel"]
        receiver_ids = parse_kudos(message["text"], giver_id, bot_id)
        if not receiver_ids:
            return

        with session_factory() as session:
            record_kudos(session, giver_id, receiver_ids, channel_id)

        client.chat_postMessage(
            channel=settings.kudos_channel or channel_id,
            text=kudos_message(giver_id, receiver_ids),
        )

    @app.event("reaction_added")
    def save_reacted_message(event, client):
        if (
            event["reaction"] != settings.save_emoji
            or event["item"]["type"] != "message"
        ):
            return

        channel_id = event["item"]["channel"]
        message_ts = event["item"]["ts"]
        saved_by = event["user"]

        with session_factory() as session:
            if already_saved(session, channel_id, message_ts):
                return

            message = fetch_message(client, channel_id, message_ts, saved_by)
            if message is None:
                return

            author_name, channel_name = message.author_name, message.channel_name
            save_message(session, message)

        logger.info("Saved message %s from %s", message_ts, channel_id)
        client.chat_postMessage(
            channel=saved_by,
            text=f":bookmark: Saved {author_name}'s message from #{channel_name}.",
        )

    @app.event({"type": "message", "subtype": "message_deleted"})
    def drop_deleted_message(event):
        channel_id = event["channel"]
        message_ts = event["deleted_ts"]
        with session_factory() as session:
            if delete_saved_message(session, channel_id, message_ts):
                logger.info(
                    "Dropped archived copy of deleted message %s in %s",
                    message_ts,
                    channel_id,
                )

    @app.event("message")
    def reply_to_dm(message, client):
        if message.get("bot_id") or message.get("channel_type") != "im":
            return

        text = message.get("text", "").strip()
        if text.lower().startswith(SEARCH_PREFIX):
            term = text[len(SEARCH_PREFIX) :].strip()
            with session_factory() as session:
                results = search_saved(session, term)
            reply = format_search_results(term, results)
        elif text.lower() == FORGET_KEYWORD:
            with session_factory() as session:
                removed = forget_author(session, message["user"])
            reply = f"Dropped {removed} message(s) you posted from the archive."
        elif text.lower() in HELP_KEYWORDS:
            reply = HELP_MSG.format(
                save_emoji=settings.save_emoji, channel_guide=format_channel_guide()
            )
        else:
            return

        client.chat_postMessage(channel=message["channel"], text=reply)

    return app
