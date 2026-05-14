# technical-seo-audit-toolkit

A Python CLI tool for technical SEO auditing focused on the problems standard platforms miss: JavaScript rendering failures, crawl misconfigurations, and HTTP-layer signal gaps.

Built for engineering teams running React, Next.js, Angular, or Vue who need infrastructure-level diagnosis, not a keyword report.

## What it audits

**Rendering delta.** Compares the raw HTTP response against a fully-rendered DOM via headless Chromium. Flags content that only exists post-render, which are indexation risks. Catches title tags, H1s, schema markup, and canonical tags that differ between what a basic crawler sees and what Googlebot's Web Rendering Service actually processes.

**Crawl infrastructure.** Audits robots.txt directives, sitemap validity, and redirect chain depth. Catches Disallow rules blocking entire sites, missing sitemap declarations, multi-hop redirect chains burning crawl budget, and crawl-delay settings throttling bot access.

**HTTP header audit.** Checks response headers for SEO-critical signals that live outside the HTML entirely. Catches X-Robots-Tag noindex headers silently killing indexation, missing HTTPS enforcement, and CDN cache presence affecting crawl performance.

## Who this is for

Engineering-led companies that migrated to a JavaScript framework and noticed organic traffic or indexation drop afterward. Technical SEO consultants who need a reproducible, scriptable audit they can run against any URL and pipe into a larger data workflow. This is not a keyword tool.

## Installation

Requires Python 3.9+

```bash
git clone https://github.com/codepan03/technical-seo-audit-toolkit.git
cd technical-seo-audit-toolkit
pip install -r requirements.txt
```

For the full rendering audit, install Chromium via Playwright:

```bash
playwright install chromium
```

## Usage

```bash
python3 cli.py --url https://yoursite.com
python3 cli.py --url https://yoursite.com --skip-render
```

Results print to terminal and save to sample_output/audit_result.json.

## Sample output
```
Technical SEO Audit Toolkit
Target: https://pypi.org

CRAWL AUDIT
  ✔  robots.txt found (HTTP 200)
  Disallow rules: 12
  Sitemap declared: True
  ✔  sitemap.xml found — 257 child sitemaps
  ✔  No redirect chain detected

HEADER AUDIT
  Status code: 200
  ✔  No x-robots-tag header (normal)
  ✔  HTTPS enforced
  ⚠  Cache-Control: not set
```
## Project structure
```
technical-seo-audit-toolkit/
├── cli.py
├── requirements.txt
├── audits/
│   ├── crawl.py
│   ├── headers.py
│   └── rendering.py
└── sample_output/
    └── audit_result.json
```
## Roadmap

GSC API integration to pull Search Console crawl stats directly into the audit pipeline. BigQuery export for multi-site time-series analysis across client portfolios. Lambda deployment to run rendering audits serverlessly via API Gateway. Cloudflare Worker templates for common edge SEO fixes without touching application code. Each item maps to a milestone in an ongoing AWS certification path.

## License

MIT
