"""On-demand Internet lead retrieval; search matches are not investment facts."""

from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse

GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
BRAVE_URL = "https://api.search.brave.com/res/v1/web/search"

THEMES = {
    "1 · Capital Preservation": {
        "Treasury and credit conditions": '("Treasury yields" OR "credit spreads")',
        "Liquidity and banking threats": '("bank liquidity" OR "deposit insurance")',
    },
    "2 · Core Compounding": {
        "Multifamily and property demand": '("multifamily occupancy" OR "apartment supply")',
        "REIT and commercial property": '("REIT earnings" OR "commercial property refinancing")',
    },
    "3 · Proven Wealth Builders": {
        "Service business acquisitions": '("HVAC acquisition" OR "veterinary acquisition" OR "IT services acquisition")',
        "Infrastructure operating demand": '("battery storage maintenance" OR "wastewater infrastructure contracts")',
        "Cannabis operations": '("cannabis dispensary acquisition" OR "cannabis wholesale license")',
    },
    "4 · Asymmetric Opportunities": {
        "AI infrastructure suppliers": '("AI data center supplier" OR "liquid cooling orders")',
        "Medical AI and robotics": '("medical AI clinical validation" OR "robotics commercial contract")',
        "Water and desalination": '("desalination contract" OR "advanced water treatment")',
    },
}


def canonical_url(url):
    """Allow public HTTP(S) result links and remove fragments for deduplication."""
    parsed = urlparse(url or "")
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return ""
    return urlunparse((parsed.scheme, parsed.netloc.lower(), parsed.path, parsed.params, parsed.query, ""))


def normalize_gdelt(payload, tier, theme, query):
    observed = datetime.now(timezone.utc).isoformat(timespec="seconds")
    results = []
    for article in payload.get("articles", []):
        url = canonical_url(article.get("url"))
        if not url:
            continue
        results.append({
            "title": article.get("title") or "Untitled article", "url": url,
            "published": article.get("seendate") or "Date not supplied",
            "source": article.get("domain") or urlparse(url).hostname,
            "tier": tier, "theme": theme, "query": query,
            "discovered_at": observed, "provider": "GDELT news index",
            "verification": "Search result only; underlying article not verified",
        })
    return results


def normalize_brave(payload, tier, theme, query):
    observed = datetime.now(timezone.utc).isoformat(timespec="seconds")
    results = []
    for item in payload.get("web", {}).get("results", []):
        url = canonical_url(item.get("url"))
        if not url:
            continue
        results.append({
            "title": item.get("title") or "Untitled page", "url": url,
            "published": item.get("page_age") or "Date not supplied",
            "source": urlparse(url).hostname, "tier": tier, "theme": theme,
            "query": query, "discovered_at": observed, "provider": "Brave web index",
            "verification": "Search result only; underlying page not verified",
        })
    return results


def search_theme(tier, theme, brave_key="", count=12):
    """Search recent global news and optionally the wider web, on demand."""
    import requests

    if tier not in THEMES or theme not in THEMES[tier]:
        raise ValueError("Choose a supported tier and theme")
    if not 1 <= count <= 20:
        raise ValueError("Count must be between 1 and 20")
    query = THEMES[tier][theme]
    response = requests.get(GDELT_URL, params={
        "query": query, "mode": "artlist", "format": "json",
        "maxrecords": count, "timespan": "1week", "sort": "datedesc",
    }, timeout=20)
    response.raise_for_status()
    leads = normalize_gdelt(response.json(), tier, theme, query)
    errors = []
    if brave_key:
        try:
            response = requests.get(BRAVE_URL, params={
                "q": query, "count": count, "freshness": "pw",
            }, headers={"X-Subscription-Token": brave_key, "Accept": "application/json"}, timeout=20)
            response.raise_for_status()
            leads.extend(normalize_brave(response.json(), tier, theme, query))
        except (requests.RequestException, ValueError) as exc:
            errors.append(f"Brave web search unavailable: {exc.__class__.__name__}")
    seen = set()
    unique = []
    for lead in leads:
        if lead["url"] not in seen:
            seen.add(lead["url"])
            unique.append(lead)
    return unique, errors


def web_context(leads, limit=16):
    if not leads:
        return "No Internet search leads are available in this session."
    lines = ["On-demand Internet search matches, not verified claims or investable deals:"]
    for lead in leads[:limit]:
        lines.append(f"- {lead['title']} | {lead['tier']} | {lead['provider']} | "
                     f"seen/published {lead['published']} | {lead['url']}")
    return "\n".join(lines)
