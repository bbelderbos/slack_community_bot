from datetime import UTC, datetime

from sqlalchemy import UniqueConstraint, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class Kudos(Base):
    __tablename__ = "kudos"

    id: Mapped[int] = mapped_column(primary_key=True)
    giver_id: Mapped[str]
    receiver_id: Mapped[str]
    channel_id: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))


class SavedMessage(Base):
    __tablename__ = "saved_messages"
    __table_args__ = (UniqueConstraint("channel_id", "message_ts"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[str]
    channel_name: Mapped[str]
    message_ts: Mapped[str]
    author_id: Mapped[str]
    author_name: Mapped[str]
    text: Mapped[str]
    permalink: Mapped[str]
    posted_at: Mapped[datetime]
    saved_by: Mapped[str]
    saved_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))


def create_session_factory(database_url: str) -> sessionmaker:
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return sessionmaker(engine)
