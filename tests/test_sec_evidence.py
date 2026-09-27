import unittest
from unittest.mock import Mock

from scoring.sec_evidence import extract_financial_evidence, match_registrant, research_public_company, suggest_registrants


def fact(value, end, start, filed="2026-03-01"):
    return {"val": value, "end": end, "start": start, "filed": filed,
            "form": "10-K", "accn": "0000000000-26-000001"}


class SECFinancialEvidenceTests(unittest.TestCase):
    def test_ambiguous_company_name_is_not_guessed(self):
        tickers = [{"title": "Acme Inc", "cik_str": 1, "ticker": "A"},
                   {"title": "Acme Corp", "cik_str": 2, "ticker": "B"}]
        self.assertIsNone(match_registrant("Acme", tickers))
        self.assertEqual(match_registrant("B", tickers)["cik_str"], 2)
        self.assertEqual(len(suggest_registrants("Acme", tickers)), 2)

    def test_reported_annual_facts_and_negative_fcf(self):
        payload = {"entityName": "Acme Inc", "facts": {"us-gaap": {
            "Revenues": {"units": {"USD": [
                fact(100, "2025-12-31", "2025-01-01"),
                fact(80, "2024-12-31", "2024-01-01", "2025-03-01"),
                fact(999, "2026-03-31", "2026-01-01"),
            ]}},
            "NetCashProvidedByUsedInOperatingActivities": {"units": {"USD": [
                fact(10, "2025-12-31", "2025-01-01")]}},
            "PaymentsToAcquirePropertyPlantAndEquipment": {"units": {"USD": [
                fact(20, "2025-12-31", "2025-01-01")]}},
        }}}
        result = extract_financial_evidence(payload, 1, "ACME", "2026-09-27")
        self.assertEqual(result["revenue"]["value"], 100)
        self.assertEqual(result["growth_pct"], 25)
        self.assertEqual(result["fcf"]["value"], -10)
        self.assertEqual(len(result["hard_stops"]), 1)

    def test_private_company_stops_before_facts_request(self):
        response = Mock()
        response.json.return_value = {"0": {"title": "Other Corp", "cik_str": 1, "ticker": "O"}}
        get = Mock(return_value=response)
        self.assertIsNone(research_public_company("Private Business", "Agent contact@example.com", get=get))
        self.assertEqual(get.call_count, 1)


if __name__ == "__main__":
    unittest.main()
