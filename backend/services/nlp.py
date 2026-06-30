from typing import TypedDict

class Entities(TypedDict):
    persons: list[str]
    orgs: list[str]
    locations: list[str]
    dates: list[str]
    events: list[str]
    all_labels: list[str]

_nlp = None

def _load_nlp():
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_sm")
        except Exception:
            _nlp = False
    return _nlp

def extract_entities(text: str) -> Entities:
    nlp = _load_nlp()
    empty: Entities = {"persons": [], "orgs": [], "locations": [], "dates": [], "events": [], "all_labels": []}
    if not nlp:
        return empty

    doc = nlp(text[:5000])
    persons, orgs, locs, dates, events = [], [], [], [], []
    for ent in doc.ents:
        val = ent.text.strip()
        if ent.label_ == "PERSON":
            persons.append(val)
        elif ent.label_ == "ORG":
            orgs.append(val)
        elif ent.label_ in ("GPE", "LOC"):
            locs.append(val)
        elif ent.label_ == "DATE":
            dates.append(val)
        elif ent.label_ == "EVENT":
            events.append(val)

    all_labels = [f"{e.text} ({e.label_})" for e in doc.ents]

    return {
        "persons": list(dict.fromkeys(persons)),
        "orgs": list(dict.fromkeys(orgs)),
        "locations": list(dict.fromkeys(locs)),
        "dates": list(dict.fromkeys(dates)),
        "events": list(dict.fromkeys(events)),
        "all_labels": all_labels,
    }
