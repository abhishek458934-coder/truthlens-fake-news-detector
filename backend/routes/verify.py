import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from ..db.database import get_db
from ..db.models import Check
from ..schemas import VerifyRequest, CheckResponse
from ..services import scraper, nlp, gemini, cache

router = APIRouter()

BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0"}

def _validate_url(url: str):
    from urllib.parse import urlparse
    p = urlparse(url)
    if p.scheme not in ("http", "https"):
        raise HTTPException(400, "Only http/https URLs are supported")
    host = p.hostname or ""
    if host in BLOCKED_HOSTS or host.startswith(("10.", "192.168.", "172.")):
        raise HTTPException(400, "Private/internal URLs are not allowed")

@router.post("/verify", response_model=CheckResponse)
async def verify(req: VerifyRequest, db: AsyncSession = Depends(get_db)):
    if not req.text and not req.url:
        raise HTTPException(400, "Provide either text or url")

    claim_text = req.text or ""

    if req.url:
        _validate_url(req.url)
        try:
            claim_text = scraper.fetch_url_text(req.url)
        except Exception as e:
            raise HTTPException(400, f"Could not fetch URL: {e}")

    if not claim_text.strip():
        raise HTTPException(400, "No text content found to analyse")
    if len(claim_text.strip()) < 10:
        raise HTTPException(400, "Claim too short — provide at least 10 characters")

    # FAISS cache check
    cached = cache.search(claim_text)
    if cached:
        record, similarity = cached
        return CheckResponse(
            **record,
            cache_hit=True,
            ml_confidence=round(similarity * 100, 1),
        )

    # spaCy NER
    entities = nlp.extract_entities(claim_text)

    # Gemini fact-check
    try:
        result = gemini.fact_check(claim_text, entities)
    except Exception as e:
        raise HTTPException(500, f"AI analysis failed: {e}")

    entity_labels = entities.get("all_labels", [])

    # Persist
    check = Check(
        input_text=claim_text[:300],
        score=result["score"],
        verdict=result["verdict"],
        reasons=json.dumps(result["reasons"]),
        official_source=result.get("official_source", ""),
        summary=result.get("summary", ""),
        entities=json.dumps(entity_labels),
        ml_confidence=None,
    )
    db.add(check)
    await db.commit()
    await db.refresh(check)

    # Add to FAISS index
    cache.add(claim_text, {
        "id": check.id,
        "input_text": check.input_text,
        "score": check.score,
        "verdict": check.verdict,
        "reasons": result["reasons"],
        "official_source": check.official_source,
        "summary": check.summary,
        "entities": entity_labels,
        "ml_confidence": None,
        "created_at": check.created_at.isoformat(),
    })

    return CheckResponse(
        id=check.id,
        input_text=check.input_text,
        score=check.score,
        verdict=check.verdict,
        reasons=result["reasons"],
        official_source=check.official_source,
        summary=check.summary,
        entities=entity_labels,
        ml_confidence=None,
        created_at=check.created_at.isoformat(),
        cache_hit=False,
    )
