import unittest

from scoring.savior_screen import web_lead_screen


class SaviorScreenTests(unittest.TestCase):
    def test_search_result_cannot_be_scored_as_investment(self):
        screen = web_lead_screen({
            "candidate_name": "Acme Energy", "title": "Acme Energy Secures Contract",
            "description": "High growth and projected returns",
        })
        self.assertEqual(screen["company"], "Acme Energy")
        self.assertEqual((screen["known_inputs"], screen["total_inputs"]), (0, 20))
        self.assertEqual(len(screen["unknown_hard_stops"]), 7)
        self.assertIn("Not estimable", screen["profit_probability"])
        self.assertIn("Unrated", screen["savior_rating"])


if __name__ == "__main__":
    unittest.main()
