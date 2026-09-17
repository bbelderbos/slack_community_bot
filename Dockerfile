FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev

ENV COMMUNITY_BOT_DATABASE_URL=sqlite:////data/community_bot.db
VOLUME /data

CMD ["uv", "run", "--no-dev", "community-bot", "run"]
