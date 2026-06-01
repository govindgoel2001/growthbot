# Automation roadmap

The full automation suite for the gobi_automates × MyHermes growth machine, in
priority order. ✅ = shipped in this repo and runnable now. 🔜 = specced, ready to
build when you give the green light + the key it needs.

| # | Automation | Status | Value | Needs from you |
|---|---|---|---|---|
| 1 | UTM attribution (`utm.py`) | ✅ | Per-reel → paid attribution in PostHog | nothing |
| 2 | Daily topic + script engine (`topic_engine.py`) | ✅ | Never run out of on-pattern ideas | `ANTHROPIC_API_KEY` |
| 3 | Long-form → clips (OpusClip) | 🔜 | 4 hrs → 30 min repurposing | OpusClip account |
| 4 | Weekly funnel watchdog (PostHog) | 🔜 | Auto-flags where activation leaks | PostHog API key |
| 5 | AI-news radar | 🔜 | Same-hour reaction posts | RSS / news API |
| 6 | AutoDM + UTM + share-CTA | 🔜 | Tracked links + sends-per-reach | your ManyChat/IG setup |
| 7 | AI-clone volume stack (year 2) | 🔜 | Daily posting at scale | HeyGen + ElevenLabs |

These pair with what already runs in **`content-bot`**: the daily competitor outlier
engine, the weekly LinkedIn visual, and the biweekly carousel→Notion pipeline.

---

## ✅ 1. UTM attribution — `scripts/utm.py`

The fix your own strategy doc marked CRITICAL: 42 AutoDM campaigns with zero UTM tags,
so PostHog can't connect a signup (or a paid subscriber) back to the reel that drove it.

```bash
# re-tag your whole export at once
python scripts/utm.py tag-csv AutoDM_List_20260526.csv AutoDM_List_tagged.csv
# one link for a new reel
python scripts/utm.py build --reel <shortcode> --path /pricing
```

After this, in PostHog break down `waitlist_signup`, `instance_started`, and
`subscription_activated` by `$initial_utm_campaign` to see which reels actually make money.

## ✅ 2. Daily topic + script engine — `scripts/topic_engine.py`

Pulls trending AI GitHub repos and writes 5 short scripts + 1 long-form outline each, in
your voice. Run locally, or on a schedule via `.github/workflows/daily-topic-engine.yml`.

**Claude-trigger alternative** (run it as a remote agent instead of GitHub Actions — paste
into a scheduled trigger at https://claude.ai/code/scheduled, cron `0 5 * * *`):

```
You are a scheduled agent for the growthbot repo. Generate today's AI content shot-list.
ANTHROPIC_API_KEY=<PASTE>
GITHUB_TOKEN=<PASTE optional>
STEPS:
1. pip install -r scripts/requirements.txt
2. python scripts/topic_engine.py --count 6 --days 14
3. git add scripts/output/ && commit "shot-list: <date>" && push to this branch.
Report the 6 repo names + one best hook each.
```

## 🔜 3. Long-form → clips (repurposing)

OpusClip's ClipAnything finds high-retention moments in your weekly long-form, reframes
vertical with captions, and exports 6–10 clips for IG/TikTok/Shorts. This is the
"record-once-post-10×" engine in §5 of the strategy. Mostly a configured external tool;
growthbot can add a small script to rename/route the exported clips + pre-fill captions
with UTM links. **Needs:** OpusClip account.

## 🔜 4. Weekly funnel watchdog (PostHog)

A scheduled job that queries your PostHog funnel (`landing_viewed → free_message_sent →
instance_started → subscription_activated`), compares week-over-week, and posts a plain-English
"here's where you're leaking + the biggest drop-off" summary to you (Telegram/email/Notion).
This keeps the activation fix (§9) honest. **Needs:** PostHog personal API key.

## 🔜 5. AI-news radar

Watches official blogs / release feeds (Anthropic, OpenAI, Google, major repos) and pings you
the moment something ships, with a ready Script-D reaction hook — so you post within the hour,
while the topic is hot. **Needs:** RSS list / a news API key.

## 🔜 6. AutoDM + UTM + share-CTA

Extends what you already run: keep the comment-trigger DM, but every delivered link is
UTM-tagged (auto, via `utm.py`) and every caption gets a SHARE trigger appended. **Needs:**
access to your ManyChat / IG automation config.

## 🔜 7. AI-clone volume stack (year-2 leverage)

The Julian Goldie play: HeyGen (your avatar) + ElevenLabs (your cloned voice) + an n8n
workflow that turns each `topic_engine` shot-list into rendered daily shorts across platforms.
This is how a small channel out-publishes big ones. Build it once the manual system is humming.
**Needs:** HeyGen + ElevenLabs accounts.
