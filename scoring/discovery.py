"""Source-backed research leads from the SEC's latest EDGAR filing feed.

A filing is a lead for diligence, not a recommendation or a forecast.
"""

from datetime import datetime
from urllib.parse import urlencode
from xml.etree import ElementTree

SEC_FEED = "https://www.sec.gov/cgi-bin/browse-edgar"
ALLOWED_FORMS = {"D", "8-K", "10-K", "10-Q"}
ATOM = "{http://www.w3.org/2005/Atom}"


def latest_filings(form, user_agent, count=40):
    """Fetch a small, current official SEC feed with identifying contact details."""
    import requests

    if form not in ALLOWED_FORMS:
        raise ValueError("Unsupported filing form")
    if not user_agent or "@" not in user_agent:
        raise ValueError("Configure SEC_USER_AGENT with an app name and contact email")
    query = urlencode({
        "action": "getcurrent", "type": form, "owner": "include",
        "count": min(max(count, 1), 100), "output": "atom",
    })
    response = requests.get(
        f"{SEC_FEED}?{query}",
        headers={"User-Agent": user_agent, "Accept": "application/atom+xml"},
        timeout=15,
    )
    response.raise_for_status()
    return parse_atom(response.content)


def parse_atom(content):
    """Return dated filing leads; ignore entries without a usable SEC link."""
    root = ElementTree.fromstring(content)
    leads = []
    seen = set()
    for entry in root.findall(f"{ATOM}entry"):
        title = (entry.findtext(f"{ATOM}title") or "").strip()
        published = (
            entry.findtext(f"{ATOM}updated")
            or entry.findtext(f"{ATOM}published")
            or ""
        ).strip()
        link = next((
            node.get("href", "") for node in entry.findall(f"{ATOM}link")
            if node.get("rel", "alternate") == "alternate"
            and node.get("href", "").startswith("https://www.sec.gov/")
        ), "")
        if not link or link in seen:
            continue
        seen.add(link)
        leads.append({
            "title": title or "Untitled filing",
            "published": published,
            "source_url": link,
            "retrieved_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "verification": "Official filing; investment merits not verified",
        })
    return leads
