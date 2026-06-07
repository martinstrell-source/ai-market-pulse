from dotenv import load_dotenv
load_dotenv(override=True)

import os
import anthropic
from tavily import TavilyClient
from utils import extract_json

claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


def investigate(item: str, why: str, search_query: str, confirm: str) -> dict:
    """Run a web search and synthesize findings for an investigate item."""

    # Search
    results = tavily.search(query=search_query, max_results=5, search_depth="advanced")
    sources = results.get("results", [])

    if not sources:
        return {"summary": "No results found.", "verdict": "inconclusive", "sources": []}

    # Format results for Claude
    context = "\n\n".join([
        f"Source: {s['url']}\nTitle: {s['title']}\nContent: {s['content'][:500]}"
        for s in sources
    ])

    prompt = f"""You are a ruthlessly skeptical AI analyst. You searched the web to investigate a news story.

Item being investigated: {item}
Why it matters: {why}
What we were trying to confirm or rule out: {confirm}

Web search results:
{context}

Based only on these results, provide a concise intelligence briefing. Be specific. Do not speculate beyond what the sources say.

Respond with JSON:
{{
  "summary": "<3-5 sentence briefing of what you found>",
  "verdict": "confirmed" or "unconfirmed" or "inconclusive" or "overhyped",
  "key_finding": "<single most important thing you found>",
  "sources_used": ["<url1>", "<url2>"]
}}"""

    message = claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}]
    )

    result = extract_json(message.content[0].text)
    return result


if __name__ == "__main__":
    import json
    result = investigate(
        item="How courts are coping with a flood of AI-generated lawsuits",
        why="AI-generated legal filings are a concrete near-term harm bridging AI capability and legal infrastructure",
        search_query="AI generated lawsuits courts filing 2025 2026",
        confirm="Whether courts have developed specific responses or policies to handle AI-generated filings"
    )
    print(json.dumps(result, indent=2))
