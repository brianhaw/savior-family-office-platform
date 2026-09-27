"""Conservative primary-source financial evidence for public-company leads."""

from datetime import date
import re

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
REVENUE_TAGS = (
    "RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet",
)
OPERATING_CASH_TAG = "NetCashProvidedByUsedInOperatingActivities"
CAPEX_TAG = "PaymentsToAcquirePropertyPlantAndEquipment"


def normalized_name(name):
    name = re.sub(r"[^a-z0-9 ]", " ", (name or "").lower())
    words = name.split()
    while words and words[-1] in {"inc", "incorporated", "corp", "corporation", "co", "company", "llc", "ltd", "limited", "plc"}:
        words.pop()
    return " ".join(words)


def match_registrant(name, tickers):
    """Never guess when more than one SEC record matches a company name."""
    target = normalized_name(name)
    if not target:
        return None
    rows = tickers.values() if isinstance(tickers, dict) else tickers
    matches = [row for row in rows if normalized_name(row.get("title")) == target]
    return matches[0] if len(matches) == 1 else None


def annual_facts(payload, tag, as_of=None):
    """Pick annual-duration USD facts in filed 10-Ks, not quarterly/TTM estimates."""
    as_of = as_of or date.today().isoformat()
    units = payload.get("facts", {}).get("us-gaap", {}).get(tag, {}).get("units", {})
    rows = []
    for fact in units.get("USD", []):
        if fact.get("form") not in ("10-K", "10-K/A") or fact.get("filed", "9999") > as_of:
            continue
        try:
            days = (date.fromisoformat(fact["end"]) - date.fromisoformat(fact["start"])).days
        except (KeyError, TypeError, ValueError):
            continue
        if 330 <= days <= 400 and isinstance(fact.get("val"), (int, float)):
            rows.append(fact)
    by_end = {}
    for row in sorted(rows, key=lambda r: (r["filed"], r.get("accn", ""))):
        by_end[row["end"]] = row
    return sorted(by_end.values(), key=lambda r: r["end"], reverse=True)


def extract_financial_evidence(payload, cik, ticker, as_of=None):
    source = FACTS_URL.format(cik=int(cik))
    revenue = next((annual_facts(payload, tag, as_of) for tag in REVENUE_TAGS
                    if annual_facts(payload, tag, as_of)), [])
    operating = annual_facts(payload, OPERATING_CASH_TAG, as_of)
    capex = annual_facts(payload, CAPEX_TAG, as_of)
    result = {"registrant": payload.get("entityName", ""), "ticker": ticker,
              "cik": int(cik), "source": source, "revenue": None,
              "growth_pct": None, "fcf": None, "hard_stops": []}
    if revenue:
        latest = revenue[0]
        result["revenue"] = {"value": latest["val"], "end": latest["end"],
                             "filed": latest["filed"], "accession": latest.get("accn", "")}
        if len(revenue) > 1 and revenue[1]["val"] > 0:
            result["growth_pct"] = round(100 * (latest["val"] / revenue[1]["val"] - 1), 2)
    if operating:
        matching_capex = next((row for row in capex if row["end"] == operating[0]["end"]), None)
        if matching_capex:
            result["fcf"] = {"value": operating[0]["val"] - matching_capex["val"],
                             "end": operating[0]["end"], "filed": operating[0]["filed"],
                             "accession": operating[0].get("accn", ""),
                             "method": "Operating cash flow minus property and equipment purchases"}
            if result["fcf"]["value"] < 0:
                result["hard_stops"].append("Negative free cash flow (Savior hard stop; verify filing context)")
    return result


def research_public_company(name, user_agent, get=None):
    """Fetch SEC ticker map and XBRL facts for an unambiguous company name."""
    if not user_agent:
        raise ValueError("SEC_USER_AGENT is required")
    if get is None:
        import requests
        get = requests.get
    headers = {"User-Agent": user_agent, "Accept": "application/json"}
    response = get(TICKERS_URL, headers=headers, timeout=20)
    response.raise_for_status()
    registrant = match_registrant(name, response.json())
    if not registrant:
        return None
    cik = int(registrant["cik_str"])
    response = get(FACTS_URL.format(cik=cik), headers=headers, timeout=20)
    response.raise_for_status()
    return extract_financial_evidence(response.json(), cik, registrant["ticker"])
