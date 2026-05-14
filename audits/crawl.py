import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def audit_crawl(base_url):
    return {
        "robots_txt": _check_robots(base_url),
        "sitemap": _check_sitemap(base_url),
        "redirect_chain": _check_redirect_chain(base_url),
    }

def _check_robots(base_url):
    robots_url = urljoin(base_url, "/robots.txt")
    try:
        r = requests.get(robots_url, headers={"User-Agent": UA}, timeout=10)
        lines = r.text.splitlines()
        disallowed = [l for l in lines if l.strip().lower().startswith("disallow")]
        sitemaps = [l for l in lines if l.strip().lower().startswith("sitemap")]
        crawl_delay = [l for l in lines if l.strip().lower().startswith("crawl-delay")]
        warnings = []
        if any("disallow: /" == d.split(":")[-1].strip().lower() for d in disallowed):
            warnings.append("CRITICAL: Disallow: / found — entire site blocked from crawling")
        if not sitemaps:
            warnings.append("No sitemap declared in robots.txt")
        return {"status": r.status_code, "found": r.status_code == 200,
                "disallow_count": len(disallowed), "sitemap_declared": len(sitemaps) > 0,
                "crawl_delay_set": len(crawl_delay) > 0, "crawl_delay_lines": crawl_delay,
                "warnings": warnings}
    except Exception as e:
        return {"found": False, "error": str(e)}

def _check_sitemap(base_url):
    sitemap_url = urljoin(base_url, "/sitemap.xml")
    try:
        r = requests.get(sitemap_url, headers={"User-Agent": UA}, timeout=10)
        if r.status_code != 200:
            return {"found": False, "status": r.status_code}
        soup = BeautifulSoup(r.content, "lxml-xml")
        urls = soup.find_all("url")
        sitemapindex = soup.find_all("sitemap")
        return {"found": True, "url_count": len(urls), "is_index": len(sitemapindex) > 0,
                "child_sitemaps": len(sitemapindex),
                "warnings": [] if urls or sitemapindex else ["Sitemap exists but contains no URLs"]}
    except Exception as e:
        return {"found": False, "error": str(e)}

def _check_redirect_chain(url):
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=10, allow_redirects=True)
        chain = [resp.url for resp in r.history] + [r.url]
        hops = len(r.history)
        return {"final_url": r.url, "hop_count": hops, "chain": chain,
                "warnings": [f"Redirect chain has {hops} hops — each hop costs crawl budget"] if hops > 1 else []}
    except Exception as e:
        return {"error": str(e)}
