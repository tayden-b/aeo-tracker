# AEO Tracker

**AEO for *features* instead of brands.** It measures which product an AI answer
engine routes a developer to for each capability — *who "owns" a feature* in the
AI's mind — how that feature is positioned, and where to win the ones you're losing.

Seeded on the secrets-management + Infrastructure-as-Code landscape; the tracked
category is swappable.

> Status: early build. Module 0 — the feature-routing primitive.

## Why
A growing share of how developers pick tools now happens inside AI answers: ask
ChatGPT "how do I rotate database credentials," and whatever it recommends shapes
the decision before any human is involved. SEO had analytics for the old channel;
this new one barely has any. AEO Tracker is a measurement layer for it.

## Stack
- **Backend:** Python (official provider SDKs + Pydantic)
- **Frontend:** (coming at M3)
- **Storage:** Postgres/Supabase (coming at M2)

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install openai python-dotenv
cp .env.example .env   # then paste your OpenAI API key into .env
python m0_raw.py
```
