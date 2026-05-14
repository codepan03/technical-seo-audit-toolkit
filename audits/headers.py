import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def audit_headers(url):
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=10, allow_redirects=True)
        headers = {k.lower(): v for k, v in r.headers.items()}
        warnings = []
        if r.status_code in [404, 410]:
            warnings.append(f"Page returned {r.status_code} — verify intentional removal")
        if r.status_code >= 500:
            warnings.append(f"Server error {r.status_code} — Googlebot will back off crawling")
        if "x-cache" not in headers and "cf-cache-status" not in headers:
            warnings.append("No CDN cache headers detected — consider CloudFront or Cloudflare for crawl performance")
        link = headers.get("link", "")
        canonical = {"present": True, "value": link} if 'rel="canonical"' in link else {"present": False, "note": "No canonical set via HTTP header"}
        xr = headers.get("x-robots-tag", "")
        xr_warnings = []
        if "noindex" in xr.lower():
            xr_warnings.append("CRITICAL: x-robots-tag contains noindex — page excluded from index")
        if "nofollow" in xr.lower():
            xr_warnings.append("nofollow set — links will not be followed")
        return {
            "status_code": r.status_code,
            "canonical_header": canonical,
            "x_robots_tag": {"present": bool(xr), "value": xr, "warnings": xr_warnings},
            "https_enforced": {"enforced": url.startswith("https://"),
                               "warnings": [] if url.startswith("https://") else ["Site not on HTTPS"]},
            "cache_control": headers.get("cache-control", "not set"),
            "content_type": headers.get("content-type", "not set"),
            "warnings": warnings,
        }
    except Exception as e:
        return {"error": str(e)}
