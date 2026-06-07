# AI Market Pulse

AI Market Pulse is an agent that filters AI news for signal over hype. It classifies items by credibility, learns from your corrections, and autonomously investigates stories worth digging into using web search.

## What it does

- Fetches RSS feeds from curated high-signal sources
- Classifies each item using Claude -- scoring signal vs. hype on a 0-10 scale
- Stores results in Supabase with deduplication across runs
- Orchestrator reasons about emerging themes, coverage gaps, and what to investigate
- Investigator runs web searches via Tavily and synthesizes findings with source citations
- Human feedback loop -- override any classification and the corrections improve future scoring
- Source validator assesses candidate feeds for quality and relevance before adding them

## Stack

- Claude Sonnet 4.6 (classifier, orchestrator, investigator)
- Tavily (web search)
- Supabase (Postgres persistence)
- Streamlit (dashboard)
- Python

## Setup

1. Clone the repo
2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your API keys:
   ```
   ANTHROPIC_API_KEY=your_key
   SUPABASE_URL=your_url
   SUPABASE_KEY=your_anon_key
   TAVILY_API_KEY=your_key
   ```
4. Create the Supabase table (see `db.py` for schema)
5. Run the app:
   ```
   streamlit run app.py
   ```

## Architecture

```
RSS feeds
  → fetcher.py       -- fetch and parse feeds
  → pipeline.py      -- deduplicate, classify, persist
  → classifier.py    -- Claude scores each item
  → db.py            -- Supabase read/write
  → app.py           -- Streamlit dashboard

Orchestrator (on demand)
  → reasons about themes, gaps, investigation targets

Investigator (on demand)
  → Tavily web search + Claude synthesis
```

## Eval

A smoke test validates the classifier against 20 ground truth cases -- 10 obvious signal (peer-reviewed papers, practitioner deployment posts) and 10 obvious hype (press releases, funding announcements, prediction pieces).

```
python eval.py
```

Current baseline: 20/20 (100%).

## Author

Martin Strell — [linkedin.com/in/martin-strell-15298a](https://linkedin.com/in/martin-strell-15298a)
