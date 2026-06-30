import os
import json
import re
from datetime import date
from google import genai
from google.genai import types

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client

def build_prompt(claim: str, entities: dict) -> str:
    today = date.today().strftime("%A, %d %B %Y")
    persons   = ", ".join(entities.get("persons", [])) or "None detected"
    orgs      = ", ".join(entities.get("orgs", []))    or "None detected"
    locations = ", ".join(entities.get("locations", [])) or "None detected"
    dates     = ", ".join(entities.get("dates", []))   or "None detected"
    events    = ", ".join(entities.get("events", []))  or "None detected"

    return f"""### ROLE
You are an elite Fact-Checking Agent with real-time Google Search access.
Your job: determine the truthfulness of the claim below with maximum accuracy.

### EXTRACTED ENTITIES (from NLP pre-processing)
Persons: {persons}
Organizations: {orgs}
Locations: {locations}
Dates: {dates}
Events: {events}

### CLAIM
"{claim[:3000]}"

### TODAY'S DATE
{today}

### CHAIN-OF-THOUGHT — follow every step, do not skip

#### STEP 1 — DECONSTRUCT
Break into atomic sub-claims. For each: Subject, Action, Timeframe (convert relative dates like "yesterday" to actual date using Today's Date), Media type (text/image/video).

#### STEP 2 — SEARCH STRATEGY
Run exactly 4 targeted Google searches:
1. "[Subject] [Action] fact check {date.today().year}"
2. "[Subject] [Action] debunked OR hoax OR fake"
3. "[Subject] [Action] official statement"
4. "[Subject] [Action] Reuters OR AFP OR AP OR BBC"

#### STEP 3 — NEGATION TRAP DETECTOR
Scan ALL results for these exact signals:
- FAKE signals: "fake", "hoax", "AI-generated", "deepfake", "debunked", "manipulated", "false claim", "no such event", "did not happen"
- VERIFIED signals: "confirmed", "official statement", "government announced", "scheduled for", "multiple sources confirm"
- UNVERIFIED signals: "no evidence found", "conflicting reports", "cannot confirm", "rumour"

STRICT LOGIC RULES — apply in this order:
- Rule 1 (Negation Override): If ANY of Reuters, AP, AFP, BBC, PIB, Alt News, BOOM, The Quint explicitly says the claim is FALSE → score 0-30, verdict "Likely Fake". No exceptions.
- Rule 2 (Future Event): If claim is about a future scheduled event confirmed by official source → score 70-85, verdict "Verified"
- Rule 3 (Visual Claim): If claim involves image/video AND any fact-checker reports visual glitches, AI artifacts, extra fingers, morphed face → score 0-20, verdict "Likely Fake"
- Rule 4 (Conflicting): If credible sources conflict each other → score 40-60, verdict "Unverified"
- Rule 5 (No Evidence): If zero credible sources found → score 35-50, verdict "Unverified"
- Rule 6 (Confirmed): If 2+ independent credible sources confirm → score 70-100, verdict "Verified"

#### STEP 4 — SCORE CALIBRATION
- 0-25: Explicitly debunked by major fact-checker
- 26-40: Strong fake signals but not explicitly debunked
- 41-60: Conflicting evidence or insufficient sources
- 61-75: Partially verified, some uncertainty remains
- 76-100: Strongly verified by multiple independent credible sources

#### STEP 5 — SOURCE QUALITY CHECK
Before finalising: Is your official_source a primary source (government site, official org, major news wire)? If not, find a better one.

### OUTPUT
Respond ONLY with raw JSON, no markdown, no backticks, nothing else:
{{
  "score": <integer 0-100>,
  "verdict": "<Likely Fake|Unverified|Verified>",
  "reasons": [
    "<Evidence 1 — name the source explicitly, quote the key phrase>",
    "<Evidence 2 — contradiction or supporting detail, name source>",
    "<Evidence 3 — contextual note, date clarification, or visual check result>"
  ],
  "official_source": "<direct URL or authoritative site — must be primary source>",
  "summary": "<one sentence: state what searches found, name the fact-checker if one debunked it>"
}}"""

def fact_check(claim: str, entities: dict) -> dict:
    client = _get_client()
    prompt = build_prompt(claim, entities)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            max_output_tokens=4096,
        ),
    )

    raw = response.text or ""
    cleaned = re.sub(r"```(?:json)?\n?", "", raw).replace("```", "").strip()
    start = cleaned.find("{")
    end   = cleaned.rfind("}")
    if start != -1 and end != -1:
        cleaned = cleaned[start:end + 1]

    result = json.loads(cleaned)
    result["score"] = max(0, min(100, int(result.get("score", 50))))
    return result
