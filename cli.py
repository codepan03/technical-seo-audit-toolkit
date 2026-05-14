import argparse
import json
import sys
from datetime import datetime
from colorama import init, Fore, Style
from audits.crawl import audit_crawl
from audits.headers import audit_headers
from audits.rendering import audit_rendering

init(autoreset=True)

def print_section(title):
    print(f"\n{Fore.CYAN}{'='*60}\n  {title}\n{'='*60}{Style.RESET_ALL}")

def print_warning(msg):
    print(f"  {Fore.YELLOW}⚠  {msg}{Style.RESET_ALL}")

def print_critical(msg):
    print(f"  {Fore.RED}✖  {msg}{Style.RESET_ALL}")

def print_ok(msg):
    print(f"  {Fore.GREEN}✔  {msg}{Style.RESET_ALL}")

def print_info(label, value):
    print(f"  {Fore.WHITE}{label}:{Style.RESET_ALL} {value}")

def display_crawl(results):
    print_section("CRAWL AUDIT — robots.txt / sitemap / redirects")
    rb = results.get("robots_txt", {})
    if rb.get("found"):
        print_ok(f"robots.txt found (HTTP {rb.get('status')})")
        print_info("Disallow rules", rb.get("disallow_count", 0))
        print_info("Sitemap declared", rb.get("sitemap_declared"))
        print_info("Crawl-delay set", rb.get("crawl_delay_set"))
        for line in rb.get("crawl_delay_lines", []):
            print_info("  Crawl-delay value", line)
        for w in rb.get("warnings", []):
            print_critical(w) if "CRITICAL" in w else print_warning(w)
    else:
        print_critical(f"robots.txt not found: {rb.get('error', 'unknown')}")
    sm = results.get("sitemap", {})
    if sm.get("found"):
        print_ok("sitemap.xml found")
        print_info("URLs in sitemap", sm.get("url_count", 0))
        print_info("Is sitemap index", sm.get("is_index"))
        if sm.get("is_index"):
            print_info("Child sitemaps", sm.get("child_sitemaps"))
        for w in sm.get("warnings", []):
            print_warning(w)
    else:
        print_warning("sitemap.xml not found at /sitemap.xml")
    rc = results.get("redirect_chain", {})
    if "error" not in rc:
        hops = rc.get("hop_count", 0)
        print_ok("No redirect chain detected") if hops == 0 else print_warning(f"Redirect chain: {hops} hop(s)")
        for i, url in enumerate(rc.get("chain", [])):
            if hops > 0:
                print_info(f"  hop {i}", url)
        for w in rc.get("warnings", []):
            print_warning(w)

def display_headers(results):
    print_section("HEADER AUDIT — canonical / x-robots-tag / HTTPS / cache")
    if "error" in results:
        print_critical(f"Header audit failed: {results['error']}")
        return
    print_info("Status code", results.get("status_code"))
    print_info("Content-Type", results.get("content_type"))
    print_info("Cache-Control", results.get("cache_control"))
    canon = results.get("canonical_header", {})
    print_ok(f"Canonical HTTP header: {canon.get('value')}") if canon.get("present") else print_info("Canonical header", canon.get("note", "not set"))
    xr = results.get("x_robots_tag", {})
    for w in xr.get("warnings", []):
        print_critical(w) if "CRITICAL" in w else print_warning(w)
    if not xr.get("present"):
        print_ok("No x-robots-tag header (normal)")
    https = results.get("https_enforced", {})
    print_ok("HTTPS enforced") if https.get("enforced") else print_critical("Site not on HTTPS")
    for w in results.get("warnings", []):
        print_warning(w)

def display_rendering(results):
    print_section("RENDERING AUDIT — raw HTTP vs. Googlebot WRS (headless Chromium)")
    raw = results.get("raw_fetch", {})
    rendered = results.get("rendered_fetch", {})
    if "error" in rendered:
        print_warning(f"Rendering audit skipped: {rendered['error']}")
        print_info("Raw title", raw.get("title"))
        print_info("Raw H1s", raw.get("h1_tags"))
        print_info("Raw word count", raw.get("word_count"))
        return
    print_info("Rendering type", results.get("rendering_type", "unknown"))
    print_info("Title (raw)", raw.get("title"))
    print_info("Title (rendered)", rendered.get("title"))
    print_info("H1 (raw)", raw.get("h1_tags"))
    print_info("H1 (rendered)", rendered.get("h1_tags"))
    print_info("Word count (raw)", raw.get("word_count"))
    print_info("Word count (rendered)", rendered.get("word_count"))
    print_info("Schema markup (raw)", raw.get("schema_markup"))
    print_info("Schema markup (rendered)", rendered.get("schema_markup"))
    print_info("Noindex signal", raw.get("noindex"))
    delta = results.get("delta", {})
    if not delta:
        print_ok("No significant rendering delta — content matches rendered state")
    else:
        print(f"\n  {Fore.RED}RENDERING DELTA DETECTED:{Style.RESET_ALL}")
        for w in results.get("warnings", []):
            print_critical(w) if "CRITICAL" in w else print_warning(w)

def run_audit(url, skip_render=False):
    print(f"\n{Fore.CYAN}Technical SEO Audit Toolkit{Style.RESET_ALL}")
    print(f"Target: {url}")
    print(f"Time:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nRunning crawl audit...", end=" ", flush=True)
    crawl_results = audit_crawl(url)
    print("done")
    print("Running header audit...", end=" ", flush=True)
    header_results = audit_headers(url)
    print("done")
    rendering_results = {}
    if not skip_render:
        print("Running rendering audit...", end=" ", flush=True)
        rendering_results = audit_rendering(url)
        print("done")
    display_crawl(crawl_results)
    display_headers(header_results)
    if not skip_render:
        display_rendering(rendering_results)
    output = {"url": url, "timestamp": datetime.now().isoformat(),
              "crawl": crawl_results, "headers": header_results, "rendering": rendering_results}
    with open("sample_output/audit_result.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n{Fore.GREEN}Full audit saved to sample_output/audit_result.json{Style.RESET_ALL}\n")

def main():
    parser = argparse.ArgumentParser(description="Technical SEO Audit Toolkit")
    parser.add_argument("--url", required=True, help="Target URL (include https://)")
    parser.add_argument("--skip-render", action="store_true", help="Skip headless rendering audit")
    args = parser.parse_args()
    if not args.url.startswith("http"):
        print(f"{Fore.RED}Error: URL must start with http:// or https://{Style.RESET_ALL}")
        sys.exit(1)
    run_audit(args.url, skip_render=args.skip_render)

if __name__ == "__main__":
    main()
