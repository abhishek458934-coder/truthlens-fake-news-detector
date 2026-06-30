import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; VerifyIt-DS/1.0; +https://verifyit.app)"
}

def fetch_url_text(url: str, max_chars: int = 5000) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    title = soup.find("title")
    title_text = title.get_text(strip=True) if title else ""
    body = ""
    for selector in ["article", "main", "[class*='article']", "[class*='content']", "body"]:
        el = soup.select_one(selector)
        if el:
            body = " ".join(el.get_text(" ", strip=True).split())
            break
    combined = f"{title_text}. {body}" if title_text else body
    return combined[:max_chars]
