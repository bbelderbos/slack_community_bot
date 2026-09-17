# community-bot

A small Slack bot for community workspaces on the free plan.

Free Slack plans don't include Workflow Builder, but they *do* include the Events
API — so this bot does the onboarding a workflow would have done. It also works
around the other free-tier limit: messages disappear after 90 days, so anything
worth keeping gets archived out of Slack before it rots.

## Features

| What | How |
|------|-----|
| **Welcome DM** | New members get a DM with a channel guide and an icebreaker |
| **Weekly wins** | Every Monday 09:00 the bot nudges #wins to share recent wins |
| **Kudos** | `@someone ++` posts a public kudos — no scores, no leaderboard |
| **Archive** | React :bookmark: on any message to save it, text and all |
| **Search** | DM the bot `search <term>` to dig the archive back up |
| **Export** | `community-bot export ./archive` writes it all to markdown |
| **Help** | DM the bot `help` |

### Kudos, not karma

`@someone ++` posts `🙌 @you gave kudos to @them`. That's the whole message —
no running total, no rank, nothing to compare yourself against. Kudos can only be
given *to other people* (self-kudos and bot-kudos are dropped), so it rewards
helping rather than posting volume.

Every kudos is still stored as a row (giver, receiver, channel, timestamp). If you
ever want scoring, it's a query — not a migration.

### The archive is the point

Slack's free tier hides messages after 90 days, and that takes permalinks with it —
including Slack's own "Saved items". So the bot stores the **message text**, not a
link to it. React :bookmark: and it captures author, channel, text, permalink and
post date into SQLite. Works on thread replies as well as top-level messages, and
saving the same message twice is a no-op.

**Public channels only.** The archive is searchable by anyone who DMs the bot, so it
only ever saves from public channels. Reactions in private channels, DMs and group
DMs are ignored — nothing private lands in the archive, so nothing private can leak
back out through `search` or `export`.

`export` then writes the whole thing to markdown, one file per channel per month
(`2026-03-general.md`) — a real backup, outside Slack, greppable.

## Setup

Create a Slack app with [socket mode](https://docs.slack.dev/tools/bolt-python/concepts/socket-mode/)
enabled.

**Bot token scopes** (OAuth & Permissions):

```
chat:write        post welcomes, kudos and search results
users:read        resolve display names for the archive
channels:read     resolve channel names for the archive
channels:history  read messages being kudos'd or saved
groups:history    read messages being kudos'd in private channels (not archived)
im:history        read DM commands (search, help)
reactions:read    see the :bookmark: reaction
```

**Event subscriptions:** `team_join`, `reaction_added`, `message.channels`,
`message.groups`, `message.im`.

**App Home:** under *Show Tabs*, enable the **Messages Tab** and tick *Allow users
to send Slash commands and messages from the messages tab*. Without this, DMs from
the bot fail with `messages_tab_disabled` — so welcomes never arrive and `search`
and `help` go unanswered.

Then copy `.env.example` to `.env` and fill in your tokens:

```env
COMMUNITY_BOT_SLACK_BOT_TOKEN=xoxb-...
COMMUNITY_BOT_SLACK_APP_TOKEN=xapp-...

# optional
COMMUNITY_BOT_DATABASE_URL=sqlite:///community_bot.db
COMMUNITY_BOT_KUDOS_CHANNEL=C0KUDOS
COMMUNITY_BOT_SAVE_EMOJI=bookmark
```

`KUDOS_CHANNEL` routes every kudos to one channel. Leave it unset and the bot
replies where the kudos happened. Invite the bot to any channel it should watch.

## Run

```bash
uv sync
uv run community-bot           # start the bot
uv run community-bot export ./archive
```

## Hosting

Socket Mode means the bot **dials out** to Slack over a websocket. Nothing needs to
reach it from the internet: no public URL, no TLS, no reverse proxy, no ingress.
You just need one always-on process and a disk that survives restarts.

**Fly.io** (a `Dockerfile` and `fly.toml` are in the repo):

```bash
fly launch --no-deploy            # claim the app name
fly volumes create community_bot_data --size 1 --region ams
fly secrets set \
  COMMUNITY_BOT_SLACK_BOT_TOKEN=xoxb-... \
  COMMUNITY_BOT_SLACK_APP_TOKEN=xapp-...
fly deploy
```

~$2/month on a 256MB shared-cpu-1x. `auto_stop_machines = false` matters: the bot
has no inbound HTTP for Fly to wake it on, so it must not be allowed to sleep.

To pull the archive down:

```bash
fly ssh console -C "uv run --no-dev community-bot export /data/archive"
fly sftp get /data/archive/2026-03-general.md
```

**Alternatives:**

- **Any VPS** — `docker compose up -d` with `/data` mounted, or systemd with
  `Restart=always`. Most control, you own backups.
- **Raspberry Pi at home** — genuinely fine here. No inbound ports needed, so no
  port forwarding or dynamic DNS. The only risk is your home internet.
- **Railway / Render** — both work; pick a *worker*-type service, not a web service,
  and attach a volume for the SQLite file.

Avoid anything serverless (Lambda, Cloud Run scale-to-zero). A Socket Mode bot is a
long-lived connection, not a request handler.

### Back up the SQLite file

The archive only helps if it outlives the host. Either `export` to markdown into a
git repo on a schedule, or copy the `.db` file off the volume — SQLite is one file.

## Customise

Community content lives in `src/community_bot/welcome.py`: `CHANNEL_GUIDE`,
`WELCOME_QUESTIONS`, `WELCOME_MSG`. The channel ids there are placeholders — swap
them for your own (in Slack: right click a channel → Copy link, the `Cxxx` part).
Add each channel's id to make the guide clickable — without it channels render as
plain `#name`.

## Develop

```bash
uv run ruff format .
uv run ruff check --fix .
uv run ty check .
uv run pytest -q
```

Slack I/O is confined to `slack.py` and the handlers in `app.py`; everything else is
pure functions over a session, which is what the tests cover.

## License

MIT
