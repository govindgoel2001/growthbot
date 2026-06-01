#!/usr/bin/env python3
"""
topic_engine.py — your daily "Broad AI -> Hermes" idea + script machine.

content-bot answers "what are my COMPETITORS doing" (outlier engine over 7 handles).
This answers "what should I post about TODAY" from the open AI world, and hands you
finished scripts — so you never run dry making hundreds of pieces.

Pipeline:
  1. Pull trending AI GitHub repos (the "free repo of the day" content you already win with).
  2. For each, Claude writes: why it matters, the Hermes bridge angle, 5 ready-to-shoot
     short-form scripts (hook / body / CTA), and 1 long-form outline — in your voice,
     reusing content-bot's anti-AI-slop style rules.
  3. Write a dated shot-list (JSON + Markdown) to output/ and (in CI) commit it.

Runs with zero keys in "topics only" mode. Add ANTHROPIC_API_KEY for scripts,
GITHUB_TOKEN to raise the GitHub rate limit.

  python topic_engine.py                 # default: 6 repos, last 14 days
  python topic_engine.py --count 8 --days 7
  python topic_engine.py --no-llm        # skip Claude, just list trending repos
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

try:
    import anthropic  # optional; only needed for script generation
except Exception:  # pragma: no cover
    anthropic = None

OUTPUT_DIR = Path(__file__).parent / "output"
GITHUB_API = "https://api.github.com/search/repositories"
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")

# AI topics worth surfacing for @gobi_automates. Tune freely.
GITHUB_TOPICS = ["ai-agent", "llm", "mcp", "rag", "ai-automation", "agents"]

_now = datetime.now(timezone.utc)
TODAY = _now.date().isoformat()

# Reuse content-bot's voice + banned-words contract so output matches your feed.
_SYSTEM = """\
You write short-form video scripts for @gobi_automates: an AI-automation creator who \
teaches normal people to run powerful AI for almost free, then funnels them to Hermes \
Agent (myhermes.cloud) — a personal AI that runs 24/7 on Telegram with persistent memory. \
Voice: builder-who-figures-it-out-in-public, concrete, no hype. Vary sentence length. \
No em-dashes as connectors. No rule-of-three lists. Never use: unlock, dive into, leverage, \
foster, robust, seamless, cutting-edge, revolutionize, in today's fast-paced world, \
landscape, crucial, game-changer, supercharge. Hooks are 7-12 words and earn the 4th second. \
Every CTA includes a SHARE trigger (sends-per-reach drives Instagram reach 3-5x more than likes)."""

_PROMPT = """\
Trending AI GitHub repo:
  name: {full_name}
  stars: {stars}  (gained recently)
  description: {description}
  url: {url}

Return JSON only, no markdown fence:
{{
  "why_it_matters": "2 sentences, concrete, no hype.",
  "hermes_angle": "1 sentence: how this bridges to running it 24/7 via Hermes Agent.",
  "tier": "broad | bridge | direct",
  "short_scripts": [
    {{"hook":"7-12 word spoken hook","body":"15-25s, show it working on screen","cta":"share trigger + comment trigger"}},
    {{"hook":"...","body":"...","cta":"..."}},
    {{"hook":"...","body":"...","cta":"..."}},
    {{"hook":"...","body":"...","cta":"..."}},
    {{"hook":"...","body":"...","cta":"..."}}
  ],
  "longform_outline": ["cold-open payoff","the stack + cost","build steps (leave a real error in)","it works / recap","CTA ladder: free signup -> myhermes.cloud -> community"]
}}"""


def log(msg: str) -> None:
    print(f"[{_now.isoformat()[:19]}] {msg}", flush=True)


def fetch_trending_repos(count: int, days: int) -> list[dict]:
    """Most-starred AI repos created in the last `days`, de-duped across topics."""
    since = (_now - timedelta(days=days)).date().isoformat()
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    seen: dict[str, dict] = {}
    for topic in GITHUB_TOPICS:
        q = f"topic:{topic} created:>{since}"
        try:
            r = requests.get(
                GITHUB_API,
                params={"q": q, "sort": "stars", "order": "desc", "per_page": 10},
                headers=headers,
                timeout=20,
            )
            r.raise_for_status()
        except Exception as e:
            log(f"  GitHub query failed for topic:{topic} -> {e}")
            continue
        for item in r.json().get("items", []):
            seen.setdefault(item["full_name"], {
                "full_name": item["full_name"],
                "url": item["html_url"],
                "stars": item.get("stargazers_count", 0),
                "description": (item.get("description") or "")[:300],
                "topics": item.get("topics", []),
            })
    repos = sorted(seen.values(), key=lambda x: x["stars"], reverse=True)
    log(f"Found {len(repos)} unique trending repos; taking top {count}")
    return repos[:count]


def generate_scripts(repo: dict) -> dict:
    if anthropic is None or not os.environ.get("ANTHROPIC_API_KEY"):
        return {}
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1400,
        system=_SYSTEM,
        messages=[{"role": "user", "content": _PROMPT.format(**repo)}],
    )
    raw = msg.content[0].text.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"why_it_matters": raw, "short_scripts": [], "longform_outline": []}


def write_outputs(items: list[dict]) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / f"{TODAY}.json").write_text(
        json.dumps({"generated_at": _now.isoformat(), "items": items}, indent=2)
    )

    lines = [f"# Daily AI shot-list — {TODAY}\n",
             f"{len(items)} trending repos turned into ready-to-shoot scripts.\n"]
    for it in items:
        r = it["repo"]
        s = it.get("scripts", {})
        lines.append(f"\n---\n\n## {r['full_name']}  ⭐{r['stars']:,}  [`{r['url']}`]({r['url']})\n")
        lines.append(f"_{r['description']}_\n")
        if s.get("why_it_matters"):
            lines.append(f"\n**Why it matters:** {s['why_it_matters']}\n")
        if s.get("hermes_angle"):
            lines.append(f"**Hermes angle ({s.get('tier','bridge')}):** {s['hermes_angle']}\n")
        for i, sc in enumerate(s.get("short_scripts", []), 1):
            lines.append(f"\n**Short {i}** — Hook: \"{sc.get('hook','')}\"  \n"
                         f"Body: {sc.get('body','')}  \n"
                         f"CTA: {sc.get('cta','')}\n")
        if s.get("longform_outline"):
            lines.append("\n**Long-form outline:** " + " -> ".join(s["longform_outline"]) + "\n")
    (OUTPUT_DIR / f"{TODAY}.md").write_text("".join(lines))
    log(f"Wrote output/{TODAY}.json and output/{TODAY}.md")


def main() -> None:
    ap = argparse.ArgumentParser(description="Daily Broad-AI -> Hermes topic + script engine")
    ap.add_argument("--count", type=int, default=6)
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--no-llm", action="store_true", help="list repos only, skip Claude")
    args = ap.parse_args()

    repos = fetch_trending_repos(args.count, args.days)
    if not repos:
        sys.exit("No trending repos found (GitHub rate limit? set GITHUB_TOKEN).")

    items = []
    for repo in repos:
        scripts = {} if args.no_llm else generate_scripts(repo)
        if scripts:
            log(f"  scripted: {repo['full_name']}")
        items.append({"repo": repo, "scripts": scripts})

    write_outputs(items)
    have_scripts = sum(1 for it in items if it.get("scripts", {}).get("short_scripts"))
    print(f"\n{len(items)} topics | {have_scripts} fully scripted | output/{TODAY}.md")


if __name__ == "__main__":
    main()
