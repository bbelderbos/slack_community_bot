import random

WINS_PROMPTS = (
    "Monday check-in :wave: What did you ship, learn, or fix last week? "
    "Post it here to kick off the week. Small wins count too.",
    "New week :rocket: What's one win from last week you're proud of? "
    "A merged PR, a bug you finally squashed, a concept that clicked. Drop it below.",
    "Fresh week, let's start it with a win :trophy: What went well for you last week? "
    "Doesn't have to be big. Progress is progress.",
    "Monday :muscle: Look back at last week: shipped something, unblocked a project, "
    "learned a new tool? Share it and set the tone for this one.",
    "New week ahead :seedling: What did you build or figure out last week? "
    "Post it here, no matter how small, and let's carry the momentum in.",
)


def wins_prompt_message(prompts: tuple[str, ...] = WINS_PROMPTS) -> str:
    return random.choice(prompts)  # noqa: S311
