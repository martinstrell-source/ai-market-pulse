import json
import re


def extract_json(text: str) -> dict:
    """Robustly extract a JSON object from a string that may contain markdown fences or extra text."""
    # Strip markdown fences
    if "```" in text:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if match:
            text = match.group(1)

    # Find outermost JSON object
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON object found in response: {text[:200]}")

    return json.loads(text[start:end])
