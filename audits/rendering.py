import requests
from bs4 import BeautifulSoup

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def audit_rendering(url):
    raw = _fetch_raw(url)
    if not PLAYWRIGHT_AVAILABLE:
        return {"raw_fetch": raw, "rendered_fetch": {"error": "Playwright not installed"}, "delta": {}, "warnings": []}
    rendered = _fetch_rendered(url)
    delta = _compute_delta(raw, rendered)
    return {"raw_fetch": raw, "rendered_fetch": rendered, "delta": delta,
            "rendering_type": _detect_rendering_type(raw, rendered), "warnings": _rendering_warnings(delta)}

def _fetch_raw(url):
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=10)
        soup = BeautifulSoup(r.text, "lxml")
        return {"status_code": r.status_code,
                "title": soup.title.string.strip() if soup.title else None,
                "h1_tags": [h.get_text(strip=True) for h in soup.find_all("h1")],
                "h2_count": len(soup.find_all("h2")),
                "word_count": len(soup.get_text().split()),
                "canonical": _get_canonical(soup),
                "noindex": _check_noindex(soup),
                "schema_markup": len(soup.find_all("script", {"type": "application/ld+json"})) > 0}
    except Exception as e:
        return {"error": str(e)}

def _fetch_rendered(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)
            content = page.content()
            browser.close()
        soup = BeautifulSoup(content, "lxml")
        return {"title": soup.title.string.strip() if soup.title else None,
                "h1_tags": [h.get_text(strip=True) for h in soup.find_all("h1")],
                "h2_count": len(soup.find_all("h2")),
                "word_count": len(soup.get_text().split()),
                "canonical": _get_canonical(soup),
                "noindex": _check_noindex(soup),
                "schema_markup": len(soup.find_all("script", {"type": "application/ld+json"})) > 0}
    except Exception as e:
        return {"error": str(e)}

def _compute_delta(raw, rendered):
    if "error" in raw or "error" in rendered:
        return {}
    delta = {}
    if raw.get("title") != rendered.get("title"):
        delta["title_mismatch"] = {"raw": raw.get("title"), "rendered": rendered.get("title")}
    if raw.get("h1_tags") != rendered.get("h1_tags"):
        delta["h1_mismatch"] = {"raw": raw.get("h1_tags"), "rendered": rendered.get("h1_tags")}
    word_diff = rendered.get("word_count", 0) - raw.get("word_count", 0)
    if abs(word_diff) > 50:
        delta["word_count_delta"] = {"raw": raw.get("word_count"), "rendered": rendered.get("word_count"), "difference": word_diff}
    if raw.get("canonical") != rendered.get("canonical"):
        delta["canonical_mismatch"] = {"raw": raw.get("canonical"), "rendered": rendered.get("canonical")}
    if not raw.get("schema_markup") and rendered.get("schema_markup"):
        delta["schema_only_in_rendered"] = True
    return delta

def _detect_rendering_type(raw, rendered):
    if "error" in rendered:
        return "unknown"
    word_diff = rendered.get("word_count", 0) - raw.get("word_count", 0)
    if word_diff > 200:
        return "CSR — significant content injected by JavaScript"
    elif word_diff > 50:
        return "Partial CSR — some content JavaScript-dependent"
    return "SSR/Static — content available in raw HTML (low indexation risk)"

def _rendering_warnings(delta):
    warnings = []
    if delta.get("title_mismatch"):
        warnings.append("Title tag differs between raw and rendered — Googlebot may index wrong title")
    if delta.get("h1_mismatch"):
        warnings.append("H1 differs between raw and rendered — primary topic signal at risk")
    if delta.get("word_count_delta", {}).get("difference", 0) > 200:
        warnings.append(f"Rendered page has {delta['word_count_delta']['difference']} more words than raw HTML — content may not be indexed")
    if delta.get("canonical_mismatch"):
        warnings.append("CRITICAL: Canonical tag differs between raw and rendered states")
    if delta.get("schema_only_in_rendered"):
        warnings.append("Schema markup only present post-render — structured data may not be processed")
    return warnings

def _get_canonical(soup):
    tag = soup.find("link", attrs={"rel": "canonical"})
    return tag.get("href", "") if tag else None

def _check_noindex(soup):
    tag = soup.find("meta", attrs={"name": "robots"})
    return "noindex" in tag.get("content", "").lower() if tag else False
