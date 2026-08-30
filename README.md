# Discord Server Health Bot v2

An advanced, modular Python Discord bot for auditing server security, roles, channels, bots, activity, configuration and overall health.

**New Versions Will come in later dates...**

**Credits:** @jveu — original inspiration/project concept.

## Highlights

- 🏥 Overall 0–100 health score
- 🛡️ Security risk audit
- 🎭 Advanced role/permission analysis
- 📁 Channel organization audit
- 🤖 Bot permission audit
- 🪝 Webhook audit
- 👥 Community/member statistics
- 📊 Activity sampling
- 💡 Prioritized recommendations
- 🗃️ SQLite health history
- 📈 Historical score tracking
- 🚨 Configurable automatic alerts
- ⏰ Scheduled health scans
- 🎛️ Interactive Discord buttons
- 🔒 Read-only auditing — no destructive actions
- Modular Python architecture

## Commands

### Reports
`/health report` — full interactive report

`/health score` — compact score

`/health security` — security audit

`/health roles` — role audit

`/health channels` — channel audit

`/health activity` — activity audit

`/health bots` — bot/integration audit

`/health history` — previous health scores

### Configuration
`/health config` — show configuration

`/health config channel` — set report/alert channel

`/health config schedule` — configure automatic scans

`/health config alerts` — enable/disable automatic alerts

## Scoring

The score is an advisory metric designed to highlight areas worth reviewing.

Categories:

- Security: 35%
- Moderation: 15%
- Organization: 15%
- Activity: 15%
- Community: 10%
- Bots/integrations: 10%

Critical findings have the largest impact.

## Privacy and limitations

The bot only analyzes information available through Discord's bot API.

Activity metrics are sampled from channels the bot can read. They should not be interpreted as complete historical analytics.

The bot does not ban, kick, delete channels, delete roles, or otherwise automatically modify your server.

## Setup

1. Install Python 3.10+.
2. Run:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env`.
4. Add your Discord bot token and test guild ID.
5. Enable **Server Members Intent** and **Message Content Intent** for the most complete audit.
6. Start:

```bash
python -m bot
```

## Recommended permissions

The bot is designed to audit using read-only access where possible.

For webhook auditing, the bot needs permission to view webhooks.

For activity analysis, it needs View Channel and Read Message History.

Administrator is **not required** for the bot itself.

Commands are restricted to server administrators by default.

## Project structure

```text
discord-server-health-bot-v2/
├── bot/
│   ├── __init__.py
│   ├── __main__.py
│   ├── config.py
│   ├── database.py
│   ├── cogs/
│   │   └── health.py
│   ├── services/
│   │   ├── auditor.py
│   │   └── scheduler.py
│   └── utils/
│       └── embeds.py
├── data/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Credits

**@jveu** — original inspiration/project concept.

This version is a new Python implementation expanded into an advanced server-health auditing system.
