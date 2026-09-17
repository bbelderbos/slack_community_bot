from typing import cast

import pytest
from slack_sdk import WebClient

from community_bot.slack import fetch_message


class FakeClient:
    def __init__(self, channel: dict):
        self._channel = channel

    def conversations_info(self, channel):
        return {"channel": self._channel}

    def conversations_replies(self, channel, ts):
        return {"messages": [{"ts": ts, "user": "U0ALEX", "text": "worth keeping"}]}

    def chat_getPermalink(self, channel, message_ts):
        return {"permalink": "https://slack.com/archives/x"}

    def users_info(self, user):
        return {"user": {"real_name": "Alex", "profile": {"display_name": "alex"}}}


def fetch(channel: dict):
    client = cast(WebClient, FakeClient(channel))
    return fetch_message(client, "C0X", "1710000000.000100", "U0ALICE")


def test_public_channel_message_is_saved():
    message = fetch({"name": "general"})

    assert message is not None
    assert message.channel_name == "general"


@pytest.mark.parametrize("flag", ["is_private", "is_im", "is_mpim"])
def test_non_public_conversations_are_ignored(flag):
    assert fetch({"name": "secret", flag: True}) is None
