from datetime import UTC, datetime

import pytest

from community_bot.db import SavedMessage, create_session_factory
from community_bot.saved import (
    SNIPPET_LENGTH,
    already_saved,
    delete_saved_message,
    forget_author,
    format_search_results,
    save_message,
    search_saved,
    snippet,
)


@pytest.fixture
def session():
    with create_session_factory("sqlite://")() as session:
        yield session


def make_message(
    text: str = "the trick with fixtures is scoping them in conftest.py",
    message_ts: str = "1710000000.000100",
    channel_name: str = "general",
    author_name: str = "alex",
    posted_at: datetime = datetime(2026, 3, 12, tzinfo=UTC),
) -> SavedMessage:
    return SavedMessage(
        channel_id="C0GENERAL",
        channel_name=channel_name,
        message_ts=message_ts,
        author_id="U0ALEX",
        author_name=author_name,
        text=text,
        permalink=f"https://slack.com/archives/C0GENERAL/p{message_ts}",
        posted_at=posted_at,
        saved_by="U0ALICE",
    )


def test_save_message_stores_the_text_not_just_a_link(session):
    save_message(session, make_message(text="keep me"))

    assert search_saved(session, "keep me")[0].text == "keep me"


def test_saving_the_same_message_twice_is_ignored(session):
    assert save_message(session, make_message()) is True
    assert save_message(session, make_message()) is False

    assert len(search_saved(session, "fixtures")) == 1


def test_different_messages_both_save(session):
    save_message(session, make_message(message_ts="1710000000.000100"))
    save_message(session, make_message(message_ts="1710000000.000200"))

    assert len(search_saved(session, "fixtures")) == 2


def test_already_saved_is_false_for_unknown_message(session):
    assert already_saved(session, "C0GENERAL", "1710000000.000100") is False


def test_search_is_case_insensitive(session):
    save_message(session, make_message(text="Async IO is tricky"))

    assert len(search_saved(session, "async io")) == 1


def test_search_without_matches_is_empty(session):
    save_message(session, make_message())

    assert search_saved(session, "kubernetes") == []


def test_search_returns_newest_first(session):
    save_message(
        session,
        make_message(message_ts="1", posted_at=datetime(2026, 1, 1, tzinfo=UTC)),
    )
    save_message(
        session,
        make_message(message_ts="2", posted_at=datetime(2026, 6, 1, tzinfo=UTC)),
    )

    assert [m.message_ts for m in search_saved(session, "fixtures")] == ["2", "1"]


def test_search_respects_the_limit(session):
    for index in range(5):
        save_message(session, make_message(message_ts=str(index)))

    assert len(search_saved(session, "fixtures", limit=2)) == 2


def test_snippet_leaves_short_text_alone():
    assert snippet("short and sweet") == "short and sweet"


def test_snippet_collapses_whitespace():
    assert snippet("line one\n\n  line two") == "line one line two"


def test_snippet_truncates_on_a_word_boundary():
    result = snippet("word " * 200)

    assert len(result) <= SNIPPET_LENGTH + 1
    assert result.endswith("…")


def test_search_results_name_author_channel_and_date(session):
    save_message(session, make_message())

    formatted = format_search_results("fixtures", search_saved(session, "fixtures"))

    assert "alex" in formatted
    assert "#general" in formatted
    assert "12 Mar 2026" in formatted


def test_search_results_say_so_when_empty():
    assert "Nothing saved" in format_search_results("kubernetes", [])


def test_delete_saved_message_removes_the_matching_row(session):
    save_message(session, make_message(text="delete me"))

    assert delete_saved_message(session, "C0GENERAL", "1710000000.000100") is True
    assert search_saved(session, "delete me") == []


def test_delete_saved_message_is_false_when_nothing_matches(session):
    assert delete_saved_message(session, "C0GENERAL", "1710000000.000100") is False


def test_delete_saved_message_leaves_other_messages_alone(session):
    save_message(session, make_message(message_ts="1710000000.000100"))
    save_message(session, make_message(message_ts="1710000000.000200"))

    delete_saved_message(session, "C0GENERAL", "1710000000.000100")

    assert [m.message_ts for m in search_saved(session, "fixtures")] == [
        "1710000000.000200"
    ]


def test_forget_author_removes_every_message_they_posted(session):
    save_message(session, make_message(message_ts="1"))
    save_message(session, make_message(message_ts="2"))

    assert forget_author(session, "U0ALEX") == 2
    assert search_saved(session, "fixtures") == []


def test_forget_author_leaves_other_authors_alone(session):
    save_message(session, make_message(message_ts="1"))
    other = make_message(message_ts="2", author_name="sam", text="sam's note")
    other.author_id = "U0SAM"
    save_message(session, other)

    assert forget_author(session, "U0ALEX") == 1
    assert [m.author_id for m in search_saved(session, "note")] == ["U0SAM"]
