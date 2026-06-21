import streamlit as st
from pipeline import run
from db import get_all, save, get_latest_briefing
from orchestrator import run_orchestrator
from source_validator import validate_source, add_source, remove_source, get_sources

st.set_page_config(page_title="AI Market Pulse", layout="wide")
st.title("AI Market Pulse")
st.caption("Signal over hype.")


# Cache the feed query so it doesn't hit Supabase on every rerun (slider drag,
# button click, etc.). Cleared explicitly after a fetch or an override save.
@st.cache_data(ttl=60)
def load_items(limit: int = 50) -> list[dict]:
    return get_all(limit=limit)

# Sidebar controls
with st.sidebar:
    st.header("Controls")
    min_signal = st.slider("Minimum signal score", 0, 10, 5)
    show_worth_reading = st.checkbox("Worth reading only", value=True)
    days_filter = st.selectbox("Show items from", [7, 14, 30, 90, 999], format_func=lambda x: "All time" if x == 999 else f"Last {x} days")
    limit = st.slider("Items to fetch", 5, 25, 10)
    if st.button("Fetch & Classify New Items", type="primary"):
        with st.spinner("Fetching and classifying..."):
            run(limit=limit)
        load_items.clear()
    if st.button("Refresh Briefing"):
        with st.spinner("Analyzing..."):
            st.session_state.briefing = run_orchestrator()
            from db import save_briefing
            save_briefing(st.session_state.briefing)

# Load latest briefing from Supabase if not in session
if "briefing" not in st.session_state:
    try:
        stored = get_latest_briefing()
        if stored:
            st.session_state.briefing = stored
    except Exception as e:
        st.warning(f"Could not load briefing: {e}")

# Tabs
tab_feed, tab_briefing, tab_sources = st.tabs(["Feed", "Briefing", "Sources"])

# Feed tab
with tab_feed:
    from datetime import datetime, timezone, timedelta
    results = load_items(limit=50)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_filter)
    filtered = [r for r in results
                if r["signal_score"] >= min_signal
                and (not show_worth_reading or r["worth_reading"])
                and (days_filter == 999 or datetime.fromisoformat(r["created_at"]) >= cutoff)]

    st.markdown(f"**{len(filtered)} items** match your filters ({len(results)} total)")
    st.divider()

    for item in sorted(filtered, key=lambda x: x["signal_score"], reverse=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"### [{item['title']}]({item['url']})")
            st.caption(f"{item['source']} · {item.get('published', '')}")
            st.markdown(f"_{item['reason']}_")
            with st.expander("Override classification"):
                override = st.slider(
                    "Your score", 0, 10,
                    value=item.get("override_score") or item["signal_score"],
                    key=f"slider_{item['url']}"
                )
                note = st.text_input(
                    "Why?",
                    value=item.get("override_note") or "",
                    key=f"note_{item['url']}"
                )
                if st.button("Save override", key=f"btn_{item['url']}"):
                    save({**item, "override_score": override, "override_note": note})
                    load_items.clear()
                    st.success("Saved")
        with col2:
            display_score = item.get("override_score") or item["signal_score"]
            color = "green" if display_score >= 7 else "orange" if display_score >= 4 else "red"
            st.markdown(f"<h2 style='color:{color};text-align:center'>{display_score}/10</h2>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:center'>{item['category']}</p>", unsafe_allow_html=True)
            if item.get("override_score"):
                st.caption("overridden")
        st.divider()

# Briefing tab
with tab_briefing:
    if "briefing" not in st.session_state:
        st.info("Click 'Run Orchestrator Briefing' in the sidebar to generate a briefing.")
    else:
        b = st.session_state.briefing
        st.markdown(f"### Summary\n{b.get('summary', '')}")
        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            if b.get("themes"):
                st.markdown("### Themes")
                for t in b["themes"]:
                    st.markdown(f"- {t}")
                st.divider()
            if b.get("investigate"):
                st.markdown("### Investigate")
                for idx, i in enumerate(b["investigate"]):
                    if isinstance(i, dict):
                        st.markdown(f"**{i.get('item', '')}**")
                        st.markdown(f"_Why:_ {i.get('why', '')}")
                        query = i.get('search', '')
                        encoded = query.replace(' ', '+')
                        search_url = f"https://www.perplexity.ai/search?q={encoded}"
                        st.markdown(f"_Search:_ [{query}]({search_url})")
                        st.markdown(f"_Confirm:_ {i.get('confirm', '')}")

                        inv_key = f"investigation_{idx}"
                        if st.button("Investigate", key=f"inv_btn_{idx}"):
                            # Imported lazily so Tavily/investigator aren't loaded
                            # on every launch — only when Investigate is clicked.
                            from investigator import investigate
                            with st.spinner("Searching and analyzing..."):
                                st.session_state[inv_key] = investigate(
                                    item=i.get("item", ""),
                                    why=i.get("why", ""),
                                    search_query=query,
                                    confirm=i.get("confirm", "")
                                )

                        if inv_key in st.session_state:
                            r = st.session_state[inv_key]
                            verdict = r.get("verdict", "")
                            color = "green" if verdict == "confirmed" else "orange" if verdict == "inconclusive" else "red" if verdict == "overhyped" else "blue"
                            st.markdown(f":{color}[**{verdict.upper()}**]")
                            st.markdown(f"{r.get('summary', '')}")
                            st.markdown(f"**Key finding:** {r.get('key_finding', '')}")
                            for src in r.get("sources_used", []):
                                st.markdown(f"- [{src}]({src})")

                        st.markdown("")
                    else:
                        st.markdown(f"- {i}")

        with col2:
            if b.get("gaps"):
                st.markdown("### Gaps")
                for idx, g in enumerate(b["gaps"]):
                    if isinstance(g, dict):
                        st.markdown(f"**{g.get('topic', '')}**")
                        st.markdown(f"_Why it matters:_ {g.get('why_matters', '')}")
                        suggested = g.get("suggested_source", "")
                        if suggested:
                            st.markdown(f"_Suggested source:_ `{suggested}`")
                            val_key = f"validation_{idx}"
                            if st.button("Validate & Add", key=f"val_btn_{idx}"):
                                with st.spinner("Validating..."):
                                    result = validate_source(
                                        name=g.get("topic", "New Source"),
                                        url=suggested,
                                        gap_topic=g.get("topic", "")
                                    )
                                    st.session_state[val_key] = result
                            if val_key in st.session_state:
                                v = st.session_state[val_key]
                                if not v["valid"]:
                                    st.error(f"Feed not accessible: {v.get('error', '')}")
                                else:
                                    rec = v["recommendation"]
                                    color = "green" if rec == "add" else "orange" if rec == "add_anyway" else "red"
                                    st.markdown(f":{color}[**{rec.upper()}**] — {v['reason']}")
                                    st.caption(f"Signal: {v.get('signal_quality')} | Gap relevance: {v.get('gap_relevance')} | Entries: {v.get('entry_count')}")
                                    if rec in ("add", "add_anyway"):
                                        label = "Confirm Add to Feed" if rec == "add" else "Add Anyway (high quality, low gap relevance)"
                                        if st.button(label, key=f"confirm_{idx}"):
                                            source_name = v.get("feed_title") or g.get("topic", "New Source")
                                            add_source(source_name, suggested)
                                            st.success(f"Added {source_name} to trusted sources")
                        st.markdown("")
                    else:
                        st.markdown(f"- {g}")
            if b.get("prioritize"):
                st.markdown("### Prioritize")
                for p in b["prioritize"]:
                    if isinstance(p, dict):
                        st.markdown(f"**{p.get('source', '')}** — {p.get('reason', '')}")
                    else:
                        st.markdown(f"- {p}")

# Sources tab
with tab_sources:
    st.markdown("### Trusted Sources")
    st.caption("These feeds are fetched and classified each run.")

    sources = get_sources()
    for source in sources:
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"**{source['source']}**")
            st.caption(source['url'])
        with col2:
            if st.button("Remove", key=f"remove_{source['url']}"):
                remove_source(source['url'])
                st.success("Removed")
                st.rerun()

    st.divider()
    st.markdown("### Add a Source Manually")
    new_name = st.text_input("Source name")
    new_url = st.text_input("RSS feed URL")
    if st.button("Add Source"):
        if new_name and new_url:
            add_source(new_name, new_url)
            st.success(f"Added {new_name}")
            st.rerun()
        else:
            st.error("Name and URL are required")
