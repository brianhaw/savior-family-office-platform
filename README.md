# Savior Family Office Investment Platform

Run with `streamlit run app.py` after installing `requirements.txt`.

## Samson

`samson_app.py` is a separate private Streamlit entry point for Samson. It
accepts a Savior Excel export for a single session and keeps chat in that
session. Deploy it with private access and its own `OPENAI_API_KEY` secret.
The existing chat in `app.py` remains available until the separate deployment
has been tested; then it can be removed from the questionnaire.

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
