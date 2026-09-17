from sqlalchemy import select
from sqlalchemy.orm import Session

from community_bot.db import SavedMessage

SNIPPET_LENGTH = 240
SEARCH_LIMIT = 10


def already_saved(session: Session, channel_id: str, message_ts: str) -> bool:
    statement = select(SavedMessage).where(
        SavedMessage.channel_id == channel_id, SavedMessage.message_ts == message_ts
    )
    return session.execute(statement).first() is not None


def save_message(session: Session, message: SavedMessage) -> bool:
    """Store a message unless that exact message is already in the archive."""
    if already_saved(session, message.channel_id, message.message_ts):
        return False

    session.add(message)
    session.commit()
    return True


def delete_saved_message(session: Session, channel_id: str, message_ts: str) -> bool:
    """Drop one archived message; True when a row was removed."""
    statement = select(SavedMessage).where(
        SavedMessage.channel_id == channel_id, SavedMessage.message_ts == message_ts
    )
    message = session.execute(statement).scalar_one_or_none()
    if message is None:
        return False

    session.delete(message)
    session.commit()
    return True


def forget_author(session: Session, author_id: str) -> int:
    """Drop every archived message this author posted; returns how many."""
    statement = select(SavedMessage).where(SavedMessage.author_id == author_id)
    messages = list(session.execute(statement).scalars().all())
    for message in messages:
        session.delete(message)
    session.commit()
    return len(messages)


def search_saved(
    session: Session, term: str, limit: int = SEARCH_LIMIT
) -> list[SavedMessage]:
    statement = (
        select(SavedMessage)
        .where(SavedMessage.text.icontains(term))
        .order_by(SavedMessage.posted_at.desc())
        .limit(limit)
    )
    return list(session.execute(statement).scalars().all())


def snippet(text: str) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= SNIPPET_LENGTH:
        return collapsed
    return collapsed[:SNIPPET_LENGTH].rsplit(" ", maxsplit=1)[0] + "…"


def format_search_results(term: str, results: list[SavedMessage]) -> str:
    if not results:
        return f'Nothing saved matching "{term}" yet.'

    found = [f'{len(results)} saved message(s) matching "{term}":\n']
    found += [
        f":bookmark: *{message.author_name}* in #{message.channel_name} — "
        f"{message.posted_at:%d %b %Y}\n"
        f"> {snippet(message.text)}\n"
        f"<{message.permalink}|view in Slack>\n"
        for message in results
    ]
    return "\n".join(found)
