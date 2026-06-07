from db import client


def get_overrides() -> list[dict]:
    result = client.table("items") \
        .select("title, source, summary, signal_score, override_score, override_note") \
        .not_.is_("override_score", "null") \
        .execute()
    return [r for r in result.data if r["override_score"] != r["signal_score"]]


def build_examples_block() -> str:
    overrides = get_overrides()
    if not overrides:
        return ""

    lines = ["Here are examples of past classifications you disagreed with and corrected:\n"]
    for r in overrides:
        lines.append(f"Title: {r['title']}")
        lines.append(f"Source: {r['source']}")
        lines.append(f"Claude scored: {r['signal_score']}/10 — You corrected to: {r['override_score']}/10")
        if r.get("override_note"):
            lines.append(f"Your reason: {r['override_note']}")
        lines.append("")

    lines.append("Use these corrections to calibrate your scoring on new items.\n")
    return "\n".join(lines)


if __name__ == "__main__":
    block = build_examples_block()
    if block:
        print(block)
    else:
        print("No overrides yet.")
