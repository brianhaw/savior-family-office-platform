# Samson: investment discovery and health monitoring

Samson is the private investment intelligence workspace. Savior is one intake
channel, not the only source of investment candidates. Samson must distinguish
verified facts, company-supplied claims, model estimates, and unknowns.

## Continuous jobs

1. **Discover:** collect dated public filings, company disclosures, sector and
   macroeconomic signals, policy changes, and licensed deal feeds when available.
   Screen opportunities against the family office mandate and hard stops before
   ranking candidates. Keep source links and observed dates on every claim.
2. **Monitor:** track actual holdings and watchlist names against their original
   thesis, key metrics, debt/liquidity, valuation, management changes, legal and
   regulatory developments, and concentration across the whole portfolio.
3. **Decide:** generate evidence-based buy, hold, investigate, reduce, or exit
   *review* alerts. Include the trigger, change since the last review, downside
   case, missing evidence, and an expiry date. No automatic trades.

## Evidence and forecast contract

Every signal stores source, source type, publication date, retrieval time,
affected asset or sector, jurisdiction, and confidence. Company-submitted
Savior answers remain unverified until independently checked. Conflicting
sources must be displayed rather than silently reconciled.

Forecasts use base, upside, and downside scenarios with explicit assumptions,
time horizons, cash-flow/valuation sensitivity, and probability ranges where
defensible. Compare each forecast with later outcomes and retain prior versions
to measure calibration. Trend momentum alone cannot establish expected return.
Separate a promising sector from an investable company and an attractive entry
price. Never present a rank as a guaranteed future winner.

## Data model

| Record | Minimum fields |
| --- | --- |
| Candidate | Name, sector, jurisdiction, source, status, first seen, mandate fit |
| Holding | Asset identifier, quantity or stake, cost basis, valuation date, liquidity, thesis, owner |
| Evidence | Source URL/document, published/retrieved dates, claim, verification status |
| Signal | Metric, prior/current values, comparison window, materiality, evidence IDs |
| Thesis | Expected drivers, disconfirming events, target horizon, review date |
| Alert | Trigger, severity, impacted exposure, evidence, recommended review action, disposition |
| Forecast | Scenario assumptions, horizon, range, model version, subsequent outcome |

The holding record is confidential and requires a private durable database with
access controls, backups, and an audit trail. Streamlit's local Excel file is
not that database. Do not store private holdings, financial statements, API
keys, or investor notes in the public GitHub repository.

## Screening and ranking

Hard stops are evaluated first: legal prohibition, sanctions exposure,
unverifiable ownership or financials, unacceptable leverage/liquidity,
concentration limits, integrity concerns, and mandate exclusions. Thresholds
are configurable and reasons are retained. An unknown result means review,
not automatic rejection or approval.

Eligible candidates are then compared on financial resilience, management and
incentives, demand durability, valuation, catalyst and timing, strategic fit,
political/legal exposure, downside protection, and portfolio diversification.
Show uncertainty and data completeness alongside score; no single numeric
score authorizes an investment.

## Briefings and escalation

The 7 a.m., 1 p.m., and 7 p.m. America/Los_Angeles briefings to the owner's
configured private email summarize new evidence, meaningful portfolio changes,
ranked opportunities, threats, and actions requiring review. Suppress repeated
unchanged items. Critical events can trigger an immediate alert after a
source-backed materiality check. Each briefing records delivery and failures.

## Build order and release gates

1. Private durable database, portfolio/watchlist import, access controls,
   audit trail, and a company intake queue. No outside submissions before this.
2. Source adapters starting with official public filings and economic series,
   plus source dates, deduplication, and failure monitoring. Licensed feeds are
   added only under their terms.
3. Hard-stop policy, evidence verification workflow, candidate ranking, and
   holding health dashboard. Validate against known historical examples.
4. Scenario forecasting with tracked assumptions and backtesting. Display
   calibration and uncertainty; keep human review for decisions.
5. Scheduled jobs and email delivery. Test timezone changes, duplicate
   prevention, source outages, stale data, and delivery failures before enabling
   the three daily messages.

Current `samson_app.py` is a private conversational prototype with an optional
single-session Savior export. It does not yet perform these continuous jobs.

Initial official source candidates: [SEC EDGAR filings and XBRL APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
and the [St. Louis Fed FRED API](https://fred.stlouisfed.org/docs/api/fred/).
FRED requires an application API key. Source availability, licensing, and
coverage must be checked before an adapter is enabled.
