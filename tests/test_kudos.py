import pytest
from sqlalchemy import select

from community_bot.db import Kudos, create_session_factory
from community_bot.kudos import kudos_message, parse_kudos, record_kudos

ALEX = "U0ALEX"
ALICE = "U0ALICE"
CAROL = "U0CAROL"
BOT = "U0BOT"


@pytest.fixture
def session():
    with create_session_factory("sqlite://")() as session:
        yield session


@pytest.mark.parametrize(
    "text, expected",
    [
        (f"kudos <@{ALEX}>++", [ALEX]),
        (f"<@{ALEX}> ++ for the review", [ALEX]),
        (f"<@{ALEX}>++ <@{CAROL}>++", [ALEX, CAROL]),
        (f"<@{ALEX}>++ and again <@{ALEX}>++", [ALEX]),
        ("great work everyone", []),
        (f"<@{ALEX}> is great", []),
        ("++", []),
    ],
)
def test_parse_kudos(text, expected):
    assert parse_kudos(text, giver_id=ALICE, bot_id=BOT) == expected


def test_cannot_thank_yourself():
    assert parse_kudos(f"<@{ALICE}>++", giver_id=ALICE, bot_id=BOT) == []


def test_thanking_the_bot_is_ignored():
    assert parse_kudos(f"<@{BOT}>++", giver_id=ALICE, bot_id=BOT) == []


def test_self_kudos_does_not_hide_others():
    text = f"<@{ALICE}>++ <@{ALEX}>++"
    assert parse_kudos(text, giver_id=ALICE, bot_id=BOT) == [ALEX]


def test_record_kudos_stores_one_row_per_receiver(session):
    record_kudos(session, ALICE, [ALEX, CAROL], "C0CHANNEL")

    rows = session.execute(select(Kudos)).scalars().all()
    assert {row.receiver_id for row in rows} == {ALEX, CAROL}
    assert all(row.giver_id == ALICE for row in rows)
    assert all(row.channel_id == "C0CHANNEL" for row in rows)


def test_recorded_kudos_are_timestamped(session):
    record_kudos(session, ALICE, [ALEX], "C0CHANNEL")

    row = session.execute(select(Kudos)).scalar_one()
    assert row.created_at is not None


def test_kudos_message_names_giver_and_receiver():
    assert (
        kudos_message(ALICE, [ALEX])
        == f":raised_hands: <@{ALICE}> gave kudos to <@{ALEX}>"
    )


def test_kudos_message_carries_no_score():
    message = kudos_message(ALICE, [ALEX])
    for user_id in (ALICE, ALEX):
        message = message.replace(user_id, "")
    assert not any(character.isdigit() for character in message)


@pytest.mark.parametrize(
    "receivers, expected",
    [
        ([ALEX], f"<@{ALEX}>"),
        ([ALEX, ALICE], f"<@{ALEX}> and <@{ALICE}>"),
        ([ALEX, ALICE, CAROL], f"<@{ALEX}>, <@{ALICE}> and <@{CAROL}>"),
    ],
)
def test_kudos_message_joins_receivers(receivers, expected):
    assert kudos_message("U0GIVER", receivers).endswith(f"gave kudos to {expected}")
