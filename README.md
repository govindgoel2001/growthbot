# growthbot

The growth operating system for **@gobi_automates** and **MyHermes.cloud**.

- **[STRATEGY.md](STRATEGY.md)** — the full plan: diagnosis from your real PostHog +
  AutoDM data, the Broad-AI→Hermes positioning, production cadence, scripts, b-roll,
  how to learn the material, the activation fix, monetization, and a 90-day timeline.
- **[docs/AUTOMATION_ROADMAP.md](docs/AUTOMATION_ROADMAP.md)** — every automation, what it
  does, what it needs from you, and copy-paste Claude-trigger prompts.

## How this relates to `content-bot`

`content-bot` watches your **competitors** (an outlier engine over 7 IG handles → spin
angles). `growthbot` covers the parts that were missing:

| Repo | Question it answers |
|---|---|
| `content-bot` | "What are my competitors doing that's working?" |
| **`growthbot`** | "What should I post about today (the broad AI world)?" + "Where is my link traffic going?" + "Give me the scripts." |

## What's inside (runnable today)

| Script | What it does | Needs |
|---|---|---|
| `scripts/utm.py` | Builds UTM-tagged MyHermes links and bulk re-tags your AutoDM export, so PostHog can finally attribute signups → paid by **reel**. (Your doc called this the critical fix.) | nothing |
| `scripts/topic_engine.py` | Pulls trending AI GitHub repos and writes **5 short-form scripts + 1 long-form outline** each, in your voice. Your daily idea machine. | `ANTHROPIC_API_KEY` (+ optional `GITHUB_TOKEN`) |
| `.github/workflows/daily-topic-engine.yml` | Runs the topic engine every morning and commits the shot-list back. | repo secrets |

## Quickstart

```bash
cp .env.example .env          # add ANTHROPIC_API_KEY
pip install -r scripts/requirements.txt

# fix attribution on your existing AutoDM export
python scripts/utm.py tag-csv AutoDM_List_20260526.csv AutoDM_List_tagged.csv

# build one tagged link for a new reel
python scripts/utm.py build --reel DYxlMMAyFcn

# generate today's shot-list (scripts for trending AI repos)
python scripts/topic_engine.py --count 6
# ...or without an API key, just list the trending repos:
python scripts/topic_engine.py --no-llm
```

To run the engine on autopilot: add `ANTHROPIC_API_KEY` (and optionally `GH_READ_TOKEN`)
as repo secrets (Settings → Secrets → Actions), enable Actions, and the daily workflow
commits a fresh `scripts/output/<date>.md` every morning.

## License

MIT.
