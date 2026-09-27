import unittest

from scoring.savior_prefill import prepare_prefill


class SaviorPrefillTests(unittest.TestCase):
    def test_only_sourced_financial_fields_are_prefilled(self):
        lead = {"candidate_name": "Acme", "url": "https://example.com/news"}
        evidence = {"registrant": "ACME Inc", "revenue": {"value": 100},
                    "growth_pct": 15, "fcf": {"value": -5},
                    "source": "https://data.sec.gov/api/xbrl/companyfacts/CIK0000000001.json"}
        prefill = prepare_prefill(lead, evidence)
        self.assertEqual(prefill["values"]["savior_company_name"], "ACME Inc")
        self.assertEqual(prefill["values"]["savior_revenue"], 100)
        self.assertEqual(prefill["values"]["savior_free_cash_flow"], -5)
        self.assertEqual(len(prefill["verified"]), 3)
        self.assertNotIn("savior_ebitda", prefill["values"])

    def test_new_lead_clears_stale_financial_prefill(self):
        prefill = prepare_prefill({"candidate_name": "Other", "url": "https://example.com"})
        self.assertEqual(prefill["verified"], [])
        self.assertEqual(prefill["values"]["savior_revenue"], 0)


if __name__ == "__main__":
    unittest.main()
