import copy
import unittest
from tools.compare_usage import compare

class BenchmarkTests(unittest.TestCase):
    def pair(self):
        row = {"pair_id": "synthetic-test", "arm": "baseline", "task_ref": "test-only", "codex_model": "fixed-model",
               "reasoning_effort": "fixed", "starting_commit": "same", "codex_input_tokens": 100,
               "codex_output_tokens": 20, "codex_cached_input_tokens": 30, "jev_input_tokens": 0,
               "jev_attempts": 0, "elapsed_seconds": 5, "quality_pass": True}
        other = copy.deepcopy(row); other.update(arm="jev", codex_input_tokens=80, jev_input_tokens=40, jev_attempts=1)
        return {"runs": [row, other]}
    def test_cached_tokens_not_double_counted(self):
        result = compare(self.pair())
        self.assertAlmostEqual(result["observed_codex_token_reduction_fraction"], 20 / 120)
    def test_missing_is_unknown_not_zero(self):
        data = self.pair(); data["runs"][1]["codex_input_tokens"] = None
        result = compare(data)
        self.assertEqual(result["matched_pairs"], 0)
        self.assertIsNone(result["observed_codex_token_reduction_fraction"])
    def test_incompatible_runs_not_compared(self):
        data = self.pair(); data["runs"][1]["starting_commit"] = "different"
        self.assertEqual(compare(data)["configuration_mismatch_pairs"], 1)
    def test_failed_quality_runs_not_hidden(self):
        data = self.pair(); data["runs"][1]["quality_pass"] = False
        result = compare(data)
        self.assertEqual(result["matched_pairs"], 1)
        self.assertFalse(result["both_arms_passed_all_checks"])
    def test_duplicate_pair_arm_rejected(self):
        data = self.pair(); data["runs"].append(data["runs"][0])
        with self.assertRaises(ValueError):
            compare(data)
    def test_no_quota_or_dollar_guesses(self):
        result = compare(self.pair())
        self.assertIsNone(result["codex_subscription_quota_savings"])
        self.assertIsNone(result["dollar_savings"])

if __name__ == "__main__":
    unittest.main()
