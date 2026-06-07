from dotenv import load_dotenv
load_dotenv(override=True)

import anthropic
import json
import os
from db import get_all
from utils import extract_json

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

with open("orchestrator_prompt.txt") as f:
    ORCHESTRATOR_PROMPT = f.read().strip()


def run_orchestrator() -> dict:
    recent = get_all(limit=20)

    if not recent:
        return {"themes": [], "gaps": [], "investigate": [], "prioritize": []}

    items_summary = "\n".join([
        f"- [{r['source']}] {r['title']} (signal={r['signal_score']}/10, category={r['category']})"
        for r in recent
    ])

    prompt = f"""Here are the most recent classified items:

{items_summary}

Analyze these and respond with JSON in this format:
{{
  "themes": ["<developing story or pattern you see>"],
  "gaps": [{{"topic": "<missing topic>", "why_matters": "<why a PM should care>", "suggested_source": "<specific blog, newsletter, or feed URL to add>"}}],
  "investigate": [{{"item": "<title>", "why": "<why it matters>", "search": "<specific search query to go deeper>", "confirm": "<what you are trying to confirm or rule out>"}}],
  "prioritize": [{{"source": "<source name>", "reason": "<why this source is worth prioritizing in the next fetch>"}}],
  "summary": "<2-3 sentence briefing on what matters right now>"
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=ORCHESTRATOR_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )

    return extract_json(message.content[0].text)


if __name__ == "__main__":
    result = run_orchestrator()
    print(json.dumps(result, indent=2))
