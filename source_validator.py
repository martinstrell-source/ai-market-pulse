from dotenv import load_dotenv
load_dotenv(override=True)

import requests
import feedparser
import anthropic
import os
from datetime import datetime, timezone
from utils import extract_json

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def fetch_feed(url: str) -> dict:
    """Try to fetch and parse an RSS feed. Returns metadata or error."""
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            return {"valid": False, "error": f"HTTP {response.status_code}"}

        parsed = feedparser.parse(response.content)
        if not parsed.entries:
            return {"valid": False, "error": "No entries found in feed"}

        # Get most recent entry date
        latest = parsed.entries[0]
        published = latest.get("published", "unknown")

        return {
            "valid": True,
            "entry_count": len(parsed.entries),
            "latest_title": latest.get("title", ""),
            "latest_published": published,
            "feed_title": parsed.feed.get("title", ""),
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}


def validate_source(name: str, url: str, gap_topic: str) -> dict:
    """Validate a candidate source and assess its relevance to the gap topic."""
    feed_data = fetch_feed(url)

    if not feed_data["valid"]:
        return {
            "url": url,
            "name": name,
            "valid": False,
            "error": feed_data["error"],
            "recommendation": "reject",
            "reason": f"Feed not accessible: {feed_data['error']}"
        }

    # Ask Claude to assess both gap relevance and general feed quality
    prompt = f"""A news feed has been suggested to fill a coverage gap.

Gap topic: {gap_topic}
Feed name: {name}
Feed URL: {url}
Feed title: {feed_data['feed_title']}
Entry count: {feed_data['entry_count']}
Most recent entry: {feed_data['latest_title']} ({feed_data['latest_published']})

Assess this feed on two dimensions independently:
1. Relevance to the specific gap topic
2. General feed quality for a senior PM tracking AI signal (low-hype, practitioner-quality, not a marketing channel)

Respond with JSON:
{{
  "gap_relevance": "high" or "medium" or "low",
  "signal_quality": "high" or "medium" or "low",
  "recommendation": "add" or "add_anyway" or "reject",
  "reason": "<one sentence explaining the recommendation>"
}}

Use "add" if relevant to the gap AND high quality.
Use "add_anyway" if not relevant to the gap but genuinely high quality and worth having.
Use "reject" if low quality or a marketing/PR channel."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}]
    )

    assessment = extract_json(message.content[0].text)
    return {
        "url": url,
        "name": name,
        "valid": True,
        "feed_title": feed_data["feed_title"],
        "entry_count": feed_data["entry_count"],
        "latest_title": feed_data["latest_title"],
        **assessment
    }


def get_sources() -> list[dict]:
    """Return the current list of feeds from fetcher.py."""
    import importlib
    import fetcher
    importlib.reload(fetcher)
    return fetcher.FEEDS


def add_source(name: str, url: str):
    """Add a validated source to fetcher.py."""
    with open("fetcher.py", "r") as f:
        content = f.read()

    new_entry = f'    {{"url": "{url}", "source": "{name}"}},\n'

    insert_marker = "]"
    feeds_end = content.rfind(insert_marker, 0, content.find("@dataclass"))
    updated = content[:feeds_end] + new_entry + content[feeds_end:]

    with open("fetcher.py", "w") as f:
        f.write(updated)


def remove_source(url: str):
    """Remove a source from fetcher.py by URL."""
    with open("fetcher.py", "r") as f:
        lines = f.readlines()

    updated = [l for l in lines if url not in l]

    with open("fetcher.py", "w") as f:
        f.writelines(updated)


if __name__ == "__main__":
    result = validate_source(
        name="Chip Huyen's Blog",
        url="https://huyenchip.com/feed.xml",
        gap_topic="ML engineering and AI deployment in production"
    )
    import json
    print(json.dumps(result, indent=2))
