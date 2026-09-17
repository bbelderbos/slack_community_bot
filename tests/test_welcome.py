from community_bot.welcome import (
    CHANNEL_GUIDE,
    WELCOME_QUESTIONS,
    Channel,
    format_channel_guide,
    mention,
    welcome_message,
)


def test_mention_links_channel_when_id_is_known():
    assert mention(Channel("general", "...", "C0GENERAL")) == "<#C0GENERAL>"


def test_mention_falls_back_to_plain_name():
    assert mention(Channel("general", "...")) == "#general"


def test_channel_guide_lists_every_channel():
    guide = format_channel_guide()
    assert all(channel.purpose in guide for channel in CHANNEL_GUIDE)


def test_welcome_message_mentions_the_new_member():
    assert "<@U0NEW>" in welcome_message("U0NEW")


def test_welcome_message_points_at_introductions():
    assert mention(CHANNEL_GUIDE[0]) in welcome_message("U0NEW")


def test_welcome_message_includes_an_icebreaker():
    message = welcome_message("U0NEW")
    assert any(question in message for question in WELCOME_QUESTIONS)


def test_welcome_message_has_no_leftover_placeholders():
    assert "{" not in welcome_message("U0NEW")
