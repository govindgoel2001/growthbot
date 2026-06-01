#!/usr/bin/env python3
"""
utm.py — the attribution fix.

Your May-27 strategy doc flagged this as CRITICAL: zero UTM tags on 42 AutoDM
campaigns, so PostHog can't tell which reel drove which signup (or which paid
subscriber). This fixes it with no external dependencies.

Two modes:

  # 1) Build a single tagged link (paste into a reel caption / AutoDM reply)
  python utm.py build --reel DYxlMMAyFcn
  python utm.py build --reel DYxlMMAyFcn --medium autodm --path /pricing

  # 2) Bulk re-tag your AutoDM export — rewrites every myhermes.cloud link in the
  #    "Auto Dm Name" column to carry utm_campaign=reel_<shortcode>, derived from
  #    each row's Content Link. Writes a new CSV you can re-import.
  python utm.py tag-csv AutoDM_List_20260526.csv AutoDM_List_tagged.csv

PostHog auto-captures utm_* as $initial_utm_source / $initial_utm_campaign, so
after this you can break down signups, instance_started, and subscription_activated
by the exact reel that drove them.
"""

import argparse
import csv
import re
import sys
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl

DEFAULT_BASE = "https://www.myhermes.cloud"

# matches www.myhermes.cloud / myhermes.cloud with optional scheme + path
MYHERMES_RE = re.compile(
    r"(https?://)?(www\.)?myhermes\.cloud(/[^\s)]*)?", re.IGNORECASE
)
# pull the shortcode out of an instagram reel/post URL
SHORTCODE_RE = re.compile(r"instagram\.com/(?:reel|p)/([A-Za-z0-9_-]+)", re.IGNORECASE)


def add_utm(url: str, source: str, medium: str, campaign: str) -> str:
    """Add/overwrite utm_* params on a URL, preserving any existing query."""
    if "://" not in url:
        url = "https://" + url.lstrip("/")
    parts = urlsplit(url)
    q = dict(parse_qsl(parts.query, keep_blank_values=True))
    q.update(
        {"utm_source": source, "utm_medium": medium, "utm_campaign": campaign}
    )
    return urlunsplit(
        (parts.scheme or "https", parts.netloc, parts.path or "/", urlencode(q), parts.fragment)
    )


def shortcode_from_link(link: str) -> str | None:
    m = SHORTCODE_RE.search(link or "")
    return m.group(1) if m else None


def cmd_build(args) -> None:
    base = args.base.rstrip("/") + (args.path if args.path.startswith("/") else "/" + args.path)
    campaign = f"reel_{args.reel}" if args.reel else args.campaign
    if not campaign:
        sys.exit("Provide --reel <shortcode> or --campaign <name>")
    print(add_utm(base, args.source, args.medium, campaign))


def cmd_tag_csv(args) -> None:
    """Rewrite myhermes.cloud links inside the AutoDM 'Auto Dm Name' column."""
    rewritten, rows_out, touched = 0, [], 0
    with open(args.infile, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        text_col = "Auto Dm Name"
        link_col = "Content Link"
        if text_col not in fields or link_col not in fields:
            sys.exit(f"Expected columns '{text_col}' and '{link_col}'. Found: {fields}")

        for row in reader:
            shortcode = shortcode_from_link(row.get(link_col, ""))
            campaign = f"reel_{shortcode}" if shortcode else "reel_unknown"
            body = row.get(text_col, "") or ""

            def _sub(m: re.Match) -> str:
                nonlocal rewritten
                rewritten += 1
                return add_utm(m.group(0), args.source, args.medium, campaign)

            new_body, n = MYHERMES_RE.subn(_sub, body)
            if n:
                touched += 1
            row[text_col] = new_body
            rows_out.append(row)

    with open(args.outfile, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows_out)

    print(f"Rows: {len(rows_out)} | rows with a myhermes link: {touched} | links tagged: {rewritten}")
    print(f"Wrote {args.outfile}")
    print("Re-import this into your AutoDM tool. PostHog will now attribute by reel_<shortcode>.")


def main() -> None:
    p = argparse.ArgumentParser(description="MyHermes UTM link builder + AutoDM re-tagger")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="build one tagged link")
    b.add_argument("--reel", help="instagram shortcode, e.g. DYxlMMAyFcn")
    b.add_argument("--campaign", help="custom campaign name (if not a reel)")
    b.add_argument("--source", default="instagram")
    b.add_argument("--medium", default="autodm")
    b.add_argument("--path", default="/")
    b.add_argument("--base", default=DEFAULT_BASE)
    b.set_defaults(func=cmd_build)

    t = sub.add_parser("tag-csv", help="bulk re-tag an AutoDM export")
    t.add_argument("infile")
    t.add_argument("outfile")
    t.add_argument("--source", default="instagram")
    t.add_argument("--medium", default="autodm")
    t.set_defaults(func=cmd_tag_csv)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
