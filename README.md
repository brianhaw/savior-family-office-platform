# Savior Family Office Investment Platform

Run with `streamlit run app.py` after installing `requirements.txt`.

## Samson

The planned discovery, monitoring, forecasting, and alert system is described
in [Samson's operating model](docs/samson-operating-model.md). The standalone
app below is a conversational prototype, not the continuous agent.

`samson_app.py` is a separate Streamlit entry point for Samson. For now,
`pages/1_Samson.py` also exposes it as its own page inside the existing private
Savior deployment; the questionnaire is the home page. Samson accepts a Savior
Excel export for a single session and keeps chat in that session. The existing
private deployment already has `OPENAI_API_KEY`; a future standalone deployment
will need its own key setting and access controls.
Its first discovery scan reads recent SEC filings on demand. Set
`SEC_USER_AGENT = "Samson Research contact@example.com"` in private secrets,
using a real monitored contact email, before using that scan. A filing is only
a research lead. No ranking, valuation, continuous scan, or forecast is active.
Internet discovery searches recent GDELT-indexed news by four-tier themes on
demand without an additional key. To add a wider web index, set
`BRAVE_SEARCH_API_KEY` in private secrets. Links and dates are search-result
metadata, not verified claims; open the original article and primary source.
Research statuses are session-only and are not part of the Portfolio Office
JSON export yet. Never commit API keys or confidential research notes.
The chat has been removed from `app.py`; select Samson from the app's page
navigation. The page setup is an interim way to work within Community Cloud's
single private app limit; it is not a separately hosted service.

`pages/2_Portfolio_Office.py` is a session-based prototype of the investment
policy, whole-portfolio inventory, diligence checklist, stress illustrations,
and decision log. Its export/import JSON allows manual continuity, but browser
refresh or session expiry clears the server-side entries. Keep the JSON private;
it can contain sensitive financial information and must not be committed.
Samson only sends those session entries to the OpenAI API if the user selects
the explicit Portfolio Office checkbox on the Samson page. The prototype does
not reconcile statements, verify private valuations, account for tax or fees
in stress arithmetic, execute decisions, or provide background monitoring.

Do not invite outside companies to use `app.py` yet. It displays internal
scores and saves submissions to non-durable local storage. A company-facing
intake needs its own submission flow, document handling, consent, and a
private persistent review queue before it can accept real confidential data.

Samson is an investment research chatbot in the app. Set `OPENAI_API_KEY` as
an environment variable or in Streamlit's secret settings. Standard chat and
briefing previews use `gpt-6-sol`; selecting Deep analysis uses `gpt-6-astra`.
You may override these with `SAMSON_MODEL` and `SAMSON_DEEP_MODEL` secrets.
Never put a key in this repo.

Samson reads the evaluations in `investment_history.xlsx`, if present. Its
conversation is held in the current Streamlit session. The briefing control is
a preview generated on demand. These records are user-entered evaluations,
not verified positions, market data, or current legal findings.

The hosted Streamlit instance's local Excel file is not durable shared storage.
To deliver three daily briefings when the app is closed, the next release needs
a private persistent database, dated research feeds, a scheduler, and a chosen
notification destination. The requested schedule is 7 a.m., 1 p.m., and
7 p.m. America/Los_Angeles. Configure the recipient and mail credentials as
deployment secrets when the scheduler is connected; do not commit them.
Do not upload holdings or private financial statements
to this public repository. Transactions still require the advisor and committee
reviews described in the Savior vetting workbook.
