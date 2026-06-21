"""Run this WHEN the app is being slow to launch:  ./venv/bin/python diagnose_launch.py

It times each step of the real launch path and hard-aborts after 90s, so the
last line printed tells you exactly which step is hanging.
"""
import time, signal, sys


def _alarm(sig, frm):
    print("\n!!! HARD TIMEOUT at 90s — the step printed just above is the hang.", flush=True)
    sys.exit(99)


signal.signal(signal.SIGALRM, _alarm)
signal.alarm(90)


def step(label):
    print(f"... {label}", flush=True)
    return time.perf_counter()


s = step("import streamlit"); import streamlit; print(f"   {time.perf_counter()-s:.2f}s")
s = step("import pipeline (fetcher, classifier, db, orchestrator)"); import pipeline; print(f"   {time.perf_counter()-s:.2f}s")
s = step("import source_validator"); import source_validator; print(f"   {time.perf_counter()-s:.2f}s")

from db import get_all, get_latest_briefing
s = step("get_latest_briefing() [Supabase network]")
try:
    get_latest_briefing()
except Exception as e:
    print("   ERR", e)
print(f"   {time.perf_counter()-s:.2f}s")

s = step("get_all(50) [Supabase network]")
try:
    get_all(50)
except Exception as e:
    print("   ERR", e)
print(f"   {time.perf_counter()-s:.2f}s")

print("ALL STEPS COMPLETED — the hang is NOT in the Python launch path.", flush=True)
print("If this finishes fast but `streamlit run` is slow, the hang is in the", flush=True)
print("Streamlit file watcher — try:  streamlit run app.py --server.fileWatcherType none", flush=True)
