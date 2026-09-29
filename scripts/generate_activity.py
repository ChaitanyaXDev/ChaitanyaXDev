#!/usr/bin/env python3
"""Generate a compact black/red GitHub activity card from GitHub GraphQL."""
from __future__ import annotations

import datetime as dt
import html
import json
import os
import sys
import urllib.request

GITHUB_API = "https://api.github.com/graphql"
LOGIN = os.environ.get("GITHUB_USERNAME", "ChaitanyaXDev")
TOKEN = os.environ.get("GITHUB_TOKEN")
OUTPUT = os.environ.get("OUTPUT_FILE", "assets/github-activity.svg")

if not TOKEN:
    raise SystemExit("GITHUB_TOKEN is required")

end = dt.datetime.now(dt.timezone.utc)
start = end - dt.timedelta(days=365)

query = r"""
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      restrictedContributionsCount
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

payload = json.dumps({
    "query": query,
    "variables": {
        "login": LOGIN,
        "from": start.isoformat().replace("+00:00", "Z"),
        "to": end.isoformat().replace("+00:00", "Z"),
    },
}).encode()

request = urllib.request.Request(
    GITHUB_API,
    data=payload,
    method="POST",
    headers={
        "Authorization": f"bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "ChaitanyaXDev-profile-activity",
    },
)

with urllib.request.urlopen(request, timeout=30) as response:
    result = json.load(response)

if result.get("errors"):
    raise SystemExit(json.dumps(result["errors"], indent=2))

collection = result["data"]["user"]["contributionsCollection"]
calendar = collection["contributionCalendar"]
days = [day for week in calendar["weeks"] for day in week["contributionDays"]]


def streak_stats(entries: list[dict]) -> tuple[int, int]:
    counts = {dt.date.fromisoformat(x["date"]): int(x["contributionCount"]) for x in entries}
    ordered = sorted(counts)
    if not ordered:
        return 0, 0

    longest = 0
    run = 0
    previous = None
    for day in ordered:
        if counts[day] > 0 and previous is not None and day == previous + dt.timedelta(days=1):
            run += 1
        elif counts[day] > 0:
            run = 1
        else:
            run = 0
        longest = max(longest, run)
        previous = day

    today = dt.datetime.now().date()
    current = 0
    cursor = today
    while cursor in counts and counts[cursor] > 0:
        current += 1
        cursor -= dt.timedelta(days=1)
    return current, longest

current_streak, longest_streak = streak_stats(days)
total = int(calendar["totalContributions"])
public_commits = int(collection["totalCommitContributions"])
private_contrib = int(collection["restrictedContributionsCount"])
prs = int(collection["totalPullRequestContributions"])
issues = int(collection["totalIssueContributions"])
reviews = int(collection["totalPullRequestReviewContributions"])


def esc(value: object) -> str:
    return html.escape(str(value))

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 380" role="img" aria-labelledby="title desc">
  <title id="title">{esc(LOGIN)} GitHub Activity</title>
  <desc id="desc">Real GitHub contribution activity for the previous year, including anonymized private contributions.</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#080808"/>
      <stop offset="100%" stop-color="#120406"/>
    </linearGradient>
    <filter id="softGlow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="6" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>

  <rect x="8" y="8" width="1084" height="364" rx="18" fill="url(#bg)" stroke="#EF4444" stroke-width="2"/>
  <rect x="8" y="8" width="1084" height="5" rx="3" fill="#DC2626" filter="url(#softGlow)"/>

  <text x="50" y="52" font-family="Fira Code, Courier New, monospace" font-size="16" font-weight="700" letter-spacing="1.4" fill="#F87171">{esc(LOGIN)} · GITHUB ACTIVITY</text>
  <text x="1048" y="52" text-anchor="end" font-family="Fira Code, Courier New, monospace" font-size="14" fill="#A1A1AA">PAST 365 DAYS</text>

  <line x1="366" y1="86" x2="366" y2="250" stroke="#3F3F46" stroke-width="1"/>
  <line x1="734" y1="86" x2="734" y2="250" stroke="#3F3F46" stroke-width="1"/>

  <g text-anchor="middle" font-family="Arial, Helvetica, sans-serif">
    <text x="184" y="145" font-size="62" font-weight="900" fill="#FFFFFF">{total}</text>
    <text x="184" y="176" font-size="16" font-weight="800" letter-spacing="2.4" fill="#EF4444">CONTRIBUTIONS</text>
    <text x="184" y="201" font-size="13" fill="#A1A1AA">PUBLIC + PRIVATE</text>

    <text x="550" y="145" font-size="62" font-weight="900" fill="#FFFFFF">{current_streak}</text>
    <text x="550" y="176" font-size="16" font-weight="800" letter-spacing="2.4" fill="#EF4444">CURRENT STREAK</text>
    <text x="550" y="201" font-size="13" fill="#A1A1AA">DAYS</text>

    <text x="916" y="145" font-size="62" font-weight="900" fill="#FFFFFF">{longest_streak}</text>
    <text x="916" y="176" font-size="16" font-weight="800" letter-spacing="2.4" fill="#EF4444">LONGEST STREAK</text>
    <text x="916" y="201" font-size="13" fill="#A1A1AA">DAYS</text>
  </g>

  <rect x="50" y="252" width="998" height="1" fill="#27272A"/>
  <text x="50" y="286" font-family="Fira Code, Courier New, monospace" font-size="13" fill="#A1A1AA">PRIVATE CONTRIBUTIONS <tspan fill="#EF4444" font-weight="800">{private_contrib}</tspan></text>
  <text x="337" y="286" font-family="Fira Code, Courier New, monospace" font-size="13" fill="#A1A1AA">PUBLIC COMMITS <tspan fill="#F3F4F6" font-weight="800">{public_commits}</tspan></text>
  <text x="544" y="286" font-family="Fira Code, Courier New, monospace" font-size="13" fill="#A1A1AA">PULL REQUESTS <tspan fill="#F3F4F6" font-weight="800">{prs}</tspan></text>
  <text x="744" y="286" font-family="Fira Code, Courier New, monospace" font-size="13" fill="#A1A1AA">ISSUES <tspan fill="#F3F4F6" font-weight="800">{issues}</tspan></text>
  <text x="874" y="286" font-family="Fira Code, Courier New, monospace" font-size="13" fill="#A1A1AA">REVIEWS <tspan fill="#F3F4F6" font-weight="800">{reviews}</tspan></text>

  <text x="50" y="333" font-family="Fira Code, Courier New, monospace" font-size="12" fill="#71717A">SOURCE · GITHUB GRAPHQL CONTRIBUTIONS COLLECTION</text>
  <text x="1050" y="333" text-anchor="end" font-family="Fira Code, Courier New, monospace" font-size="12" fill="#71717A">UPDATED {end.strftime('%Y-%m-%d')}</text>
</svg>\n'''

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
with open(OUTPUT, "w", encoding="utf-8") as file:
    file.write(svg)

print(f"Generated {OUTPUT}: total={total}, private={private_contrib}, current={current_streak}, longest={longest_streak}")

