import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv(override=True)

client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


def seen(url: str) -> bool:
    result = client.table("items").select("url").eq("url", url).execute()
    return len(result.data) > 0


def save(item: dict):
    client.table("items").upsert(item, on_conflict="url").execute()


def get_all(limit: int = 100) -> list[dict]:
    result = client.table("items").select("*").order("created_at", desc=True).limit(limit).execute()
    return result.data


def save_briefing(briefing: dict):
    client.table("briefings").insert({
        "summary": briefing.get("summary"),
        "themes": briefing.get("themes"),
        "gaps": briefing.get("gaps"),
        "investigate": briefing.get("investigate"),
        "prioritize": briefing.get("prioritize"),
    }).execute()


def get_latest_briefing() -> dict | None:
    result = client.table("briefings").select("*").order("created_at", desc=True).limit(1).execute()
    return result.data[0] if result.data else None
