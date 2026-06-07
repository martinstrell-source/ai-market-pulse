from dotenv import load_dotenv
load_dotenv(override=True)

import json
from classifier import classify_item

def run_eval():
    with open("eval_cases.json") as f:
        cases = json.load(f)

    results = []
    passed = 0
    failed = 0

    print(f"Running eval on {len(cases)} cases...\n")

    for case in cases:
        result = classify_item(case["title"], case["summary"], case["source"])
        score = result["signal_score"]
        expected = case["expected"]

        if expected == "signal":
            ok = score >= case["min_score"]
        else:
            ok = score <= case["max_score"]

        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1

        results.append({**case, "actual_score": score, "passed": ok})
        print(f"[{status}] {case['title'][:60]}")
        print(f"  expected={expected} | score={score}/10 | reason={result['reason'][:80]}\n")

    print("-" * 60)
    print(f"Results: {passed}/{len(cases)} passed ({100*passed//len(cases)}%)")
    print(f"Signal cases: {sum(1 for r in results if r['expected']=='signal' and r['passed'])}/{sum(1 for r in results if r['expected']=='signal')}")
    print(f"Hype cases:   {sum(1 for r in results if r['expected']=='hype' and r['passed'])}/{sum(1 for r in results if r['expected']=='hype')}")

    return results

if __name__ == "__main__":
    run_eval()
