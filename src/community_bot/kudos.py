import re

from sqlalchemy.orm import Session

from community_bot.db import Kudos

KUDOS_PATTERN = re.compile(r"<@([UW][A-Z0-9]+)>\s*\+\+")


def parse_kudos(text: str, giver_id: str, bot_id: str) -> list[str]:
    """Slack ids given kudos in this message, minus the sender and the bot itself."""
    receivers = set(KUDOS_PATTERN.findall(text))
    return sorted(receivers - {giver_id, bot_id})


def record_kudos(
    session: Session, giver_id: str, receiver_ids: list[str], channel_id: str
) -> None:
    session.add_all(
        [
            Kudos(giver_id=giver_id, receiver_id=receiver_id, channel_id=channel_id)
            for receiver_id in receiver_ids
        ]
    )
    session.commit()


def kudos_message(giver_id: str, receiver_ids: list[str]) -> str:
    mentions = [f"<@{receiver_id}>" for receiver_id in receiver_ids]
    receivers = " and ".join(filter(None, [", ".join(mentions[:-1]), mentions[-1]]))
    return f":raised_hands: <@{giver_id}> gave kudos to {receivers}"
