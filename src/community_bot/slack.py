import logging
from datetime import UTC, datetime

from slack_sdk import WebClient

from community_bot.db import SavedMessage

logger = logging.getLogger(__name__)


def _display_name(client: WebClient, user_id: str) -> str:
    profile = client.users_info(user=user_id)["user"]
    return profile["profile"].get("display_name") or profile["real_name"]


def _is_public(channel: dict) -> bool:
    return not (
        channel.get("is_private") or channel.get("is_im") or channel.get("is_mpim")
    )


def fetch_message(
    client: WebClient, channel_id: str, message_ts: str, saved_by: str
) -> SavedMessage | None:
    """Build an archive row from a public-channel message, top level or thread reply."""
    channel = client.conversations_info(channel=channel_id)["channel"]
    if not _is_public(channel):
        logger.info("Ignoring save from non-public channel %s", channel_id)
        return None

    thread = client.conversations_replies(channel=channel_id, ts=message_ts)
    message = next(
        (reply for reply in thread["messages"] if reply["ts"] == message_ts), None
    )
    if message is None:
        logger.warning(
            "Message %s in %s vanished before saving", message_ts, channel_id
        )
        return None

    permalink = client.chat_getPermalink(channel=channel_id, message_ts=message_ts)[
        "permalink"
    ]

    return SavedMessage(
        channel_id=channel_id,
        channel_name=channel["name"],
        message_ts=message_ts,
        author_id=message["user"],
        author_name=_display_name(client, message["user"]),
        text=message["text"],
        permalink=permalink,
        posted_at=datetime.fromtimestamp(float(message_ts), UTC),
        saved_by=saved_by,
    )
