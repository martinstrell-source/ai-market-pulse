from dotenv import load_dotenv
load_dotenv(override=True)

import anthropic
import json
import os
from feedback import build_examples_block
from utils import extract_json

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

with open("prompt.txt") as f:
    BASE_PROMPT = f.read().strip()

def get_system_prompt() -> str:
    examples = build_examples_block()
    if examples:
        return f"{BASE_PROMPT}\n\n{examples}"
    return BASE_PROMPT

def classify_item(title: str, summary: str, source: str) -> dict:
    prompt = f"""Classify this AI news item:

Title: {title}
Source: {source}
Summary: {summary}

Respond with JSON in this exact format:
{{
  "category": "research|deployment|tooling|hype|opinion",
  "signal_score": <0-10, where 10 is pure signal and 0 is pure hype>,
  "confidence": <0-10>,
  "reason": "<one sentence explaining your score>",
  "worth_reading": <true|false>
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        system=get_system_prompt(),
        messages=[{"role": "user", "content": prompt}]
    )

    return extract_json(message.content[0].text)


if __name__ == "__main__":
    # Test with a sample item
    result = classify_item(
        title="Anthropic Releases Claude 4 with Breakthrough Reasoning Capabilities",
        summary="Anthropic today announced Claude 4, claiming it achieves human-level reasoning on standard benchmarks. The company raised $2B in its latest funding round.",
        source="TechCrunch"
    )
    print(json.dumps(result, indent=2))
