import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


def seen(url: str) -> bool:
    result = client.table("items").select("url").eq("url", url).execute()
    return len(result.data) > 0


def save(item: dict):
    client.table("items").upsert(item, on_conflict="url").execute()


def get_all(limit: int = 100) -> list[dict]:
    result = client.table("items").select("*").order("created_at", desc=True).limit(limit).execute()
    return result.data
