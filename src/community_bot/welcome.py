import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Channel:
    name: str
    purpose: str
    channel_id: str = ""


# These are placeholder channel ids — swap them for your own. In Slack:
# right click a channel -> Copy link, the Cxxx part is the id. Adding it makes
# the channel render as a live mention; without it you get a plain #name.
# introductions must stay first — the welcome DM points new members there.
CHANNEL_GUIDE = (
    Channel("introductions", "say hi and introduce yourself", "C000INTRO"),
    Channel("general", "anything that doesn't fit elsewhere", "C000GENERAL"),
    Channel("help", "stuck on something? ask here", "C000HELP"),
    Channel("showcase", "share what you're building", "C000SHOWCASE"),
    Channel("resources", "articles, tools and links worth sharing", "C000RESOURCES"),
    Channel("wins", "shipped something? celebrate it here", "C000WINS"),
)

WELCOME_QUESTIONS = (
    "What are you building right now?",
    "What's the one thing you'd most like to get better at this year?",
    "What got you into this in the first place?",
    "What does your current setup look like?",
    "What's a tool you've started using recently that you'd recommend?",
    "What brought you to this community?",
    "What's the hardest problem you've solved lately?",
    "What does a good day of work look like for you?",
)

WELCOME_MSG = """Welcome to the community, {user}! :wave:

I'm the community bot — here's how to get started.

*Where to go*
{channel_guide}

*Say hi*
Drop an intro in {introductions}. To break the ice: _{question}_

*One more thing*
When someone helps you out, thank them with `@them ++` — I'll pass it on. \
No scores, no leaderboards, just credit where it's due.

Glad you're here. — the team
"""


def mention(channel: Channel) -> str:
    return f"<#{channel.channel_id}>" if channel.channel_id else f"#{channel.name}"


def format_channel_guide(channels: tuple[Channel, ...] = CHANNEL_GUIDE) -> str:
    return "\n".join(
        f"• {mention(channel)} — {channel.purpose}" for channel in channels
    )


def welcome_message(user_id: str) -> str:
    return WELCOME_MSG.format(
        user=f"<@{user_id}>",
        channel_guide=format_channel_guide(),
        introductions=mention(CHANNEL_GUIDE[0]),
        question=random.choice(WELCOME_QUESTIONS),  # noqa: S311
    )
