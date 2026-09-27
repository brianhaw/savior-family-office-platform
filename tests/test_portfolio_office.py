import unittest

from scoring.portfolio_office import TIERS, default_policy, stress, summarize, validate_snapshot


class PortfolioOfficeTests(unittest.TestCase):
    def setUp(self):
        self.tiers = list(TIERS)
        self.policy = default_policy()
        self.policy["annual_cash_need"] = 120_000
        self.holdings = [
            {"name": "Reserve", "tier": self.tiers[0], "value": 100_000,
             "liquid_30d": True, "unfunded": 25_000, "debt": 0,
             "verified": True, "valuation_date": "2026-09-27"},
            {"name": "Business", "tier": self.tiers[2], "value": 300_000,
             "liquid_30d": False, "unfunded": 0, "debt": 50_000,
             "verified": False, "valuation_date": "2026-06-01"},
        ]

    def test_liquidity_and_concentration_are_flagged(self):
        report = summarize(self.holdings, self.policy)
        self.assertEqual(report["weights"][self.tiers[2]], 75)
        self.assertEqual(report["required_liquidity"], 145_000)
        self.assertTrue(any("liquidity" in flag.lower() for flag in report["flags"]))
        self.assertTrue(any("Business" in flag for flag in report["flags"]))

    def test_stress_arithmetic_keeps_debt_separate(self):
        shocks = {tier: -50 for tier in self.tiers}
        shocks[self.tiers[0]] = -10
        result = stress(self.holdings, shocks)
        self.assertEqual((result["before"], result["change"], result["after"]),
                         (400_000, -160_000, 240_000))

    def test_import_rejects_invalid_policy_before_replacing_state(self):
        snapshot = {"schema": 1, "policy": self.policy,
                    "holdings": self.holdings, "diligence": [], "decisions": []}
        self.assertEqual(validate_snapshot(snapshot)["holdings"], self.holdings)
        bad = dict(snapshot, policy=dict(self.policy, targets={t: 50 for t in self.tiers}))
        with self.assertRaises(ValueError):
            validate_snapshot(bad)


if __name__ == "__main__":
    unittest.main()
