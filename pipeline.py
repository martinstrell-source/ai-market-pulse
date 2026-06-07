from fetcher import fetch_all
from classifier import classify_item
from db import seen, save
import json

def run(limit: int = 5):
    print("Fetching feeds...")
    items = fetch_all()
    print(f"Fetched {len(items)} items, classifying up to {limit} new ones...\n")

    results = []
    classified = 0
    for item in items:
        if classified >= limit:
            break
        if seen(item.url):
            print(f"[skip] {item.title}")
            continue
        try:
            classification = classify_item(item.title, item.summary, item.source)
            result = {**vars(item), **classification}
            save(result)
            results.append(result)
            classified += 1
            print(f"[{item.source}] {item.title}")
            print(f"  category={classification['category']} signal={classification['signal_score']}/10 worth_reading={classification['worth_reading']}")
            print(f"  {classification['reason']}\n")
        except Exception as e:
            print(f"Error classifying '{item.title}': {e}\n")

    return results

if __name__ == "__main__":
    run(limit=5)
