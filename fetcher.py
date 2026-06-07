import feedparser
import requests
from dataclasses import dataclass
from typing import Optional


def is_english(text: str) -> bool:
    """Simple check -- if more than 30% of characters are non-ASCII, skip it."""
    if not text:
        return True
    non_ascii = sum(1 for c in text if ord(c) > 127)
    return (non_ascii / len(text)) < 0.3

FEEDS = [
    {"url": "https://simonwillison.net/atom/everything/", "source": "Simon Willison"},
    {"url": "https://jack-clark.net/feed/", "source": "Import AI"},
    {"url": "https://www.technologyreview.com/feed/", "source": "MIT Tech Review"},
    {"url": "https://huggingface.co/blog/feed.xml", "source": "Hugging Face"},
    {"url": "https://thegradient.pub/rss/", "source": "The Gradient"},
    {"url": "https://evals.alignment.org/blog/rss.xml", "source": "ARC Evals"},
]

@dataclass
class FeedItem:
    title: str
    summary: str
    source: str
    url: str
    published: Optional[str] = None


def fetch_all() -> list[FeedItem]:
    items = []
    for feed in FEEDS:
        try:
            response = requests.get(feed["url"], timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            parsed = feedparser.parse(response.content)
            for entry in parsed.entries[:5]:
                title = entry.get("title", "")
                if not is_english(title):
                    continue
                items.append(FeedItem(
                    title=title,
                    summary=entry.get("summary", "")[:500],
                    source=feed["source"],
                    url=entry.get("link", ""),
                    published=entry.get("published", None),
                ))
        except Exception as e:
            print(f"Error fetching {feed['source']}: {e}")
    return items


if __name__ == "__main__":
    items = fetch_all()
    print(f"Fetched {len(items)} items")
    for item in items[:3]:
        print(f"\n[{item.source}] {item.title}")
