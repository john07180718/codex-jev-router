from __future__ import annotations
import copy
import io
import json
import os
import subprocess
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from jev_workflow.cli import demo_request, main
from jev_workflow.config import DEFAULTS, PolicyError, atomic_json, canonical_project, load_config
from jev_workflow.ledger import Ledger
from jev_workflow.runner import Workflow, call_worker
from jev_workflow.schema import validate_request, validate_response


def valid_response(payload: bytes) -> dict:
    data = json.loads(payload)
    answers = {}
    for name, q in data["questions"].items():
        if q["type"] == "choice":
            choice = next(k for k in q["criteria"] if k != "NEEDS_REVIEW")
            answers[name] = {"type": "choice", "choice": choice, "confidence": 1.0,
                             "probabilities": {k: float(k == choice) for k in q["criteria"]}}
        elif q["type"] == "score":
            answers[name] = {"type": "score", "score": 0.0, "confidence": 1.0,
                             "legend": {str(i): x for i, x in enumerate(q["criteria"])},
                             "probabilities": {str(i): float(i == 0) for i in range(len(q["criteria"]))}}
        else:
            answers[name] = {"type": "noul", "noul": 0.8}
    return {"ok": True, "response": {"model": "jev-1.13.0", "answers": answers,
                                    "usage": {"input_tokens": 100, "output_tokens": 20}}}


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.home = self.root / "home"
        self.cfg = copy.deepcopy(DEFAULTS)
        self.cfg.update(mode="live", authorized_projects=[canonical_project(self.project)])
        self.save()
        self.calls = []
        def fake(payload, key, timeout):
            self.calls.append((payload, key, timeout))
            return valid_response(payload)
        self.flow = Workflow(self.home, fake)
        self.task = self.flow.ledger.begin(canonical_project(self.project))
        self.req = demo_request()
        self.env = patch.dict(os.environ, {"TYPESAFE_API_KEY": "unit-testing-credential", "JEV_WORKFLOW_DISABLED": "0"})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.flow.close()
        self.tmp.cleanup()

    def save(self):
        atomic_json(self.home / "config.json", self.cfg)

    def ask(self, req=None, task=None, project=None):
        return self.flow.ask(str(project or self.project), task or self.task, req or self.req)

    def test_valid_live_is_only_advisory(self):
        out = self.ask()
        self.assertEqual(out["status"], "ADVISORY")
        self.assertTrue(out["advisory_only"])
        self.assertFalse(out["authorization_granted"])
        self.assertEqual(out["jev_usage"]["input_tokens"], 100)
        self.assertIsNone(out["codex_usage"])

    def test_no_metadata_sent_to_provider(self):
        self.ask()
        body = json.loads(self.calls[0][0])
        self.assertEqual(set(body), {"model", "state", "questions"})
        self.assertNotIn(self.task, self.calls[0][0].decode())
        self.assertNotIn(str(self.project), self.calls[0][0].decode())

    def test_mock_never_calls_transport(self):
        self.cfg["mode"] = "mock"; self.save()
        out = self.ask()
        self.assertEqual(out["status"], "MOCK")
        self.assertEqual(out["answers"]["category"]["choice"], "NEEDS_REVIEW")
        self.assertEqual(len(self.calls), 0)
        self.assertIsNone(out["jev_usage"])

    def test_off_skips(self):
        self.cfg["mode"] = "off"; self.save()
        self.assertEqual(self.ask()["reason"], "disabled")
        self.assertFalse(self.calls)

    def test_kill_switch_wins(self):
        with patch.dict(os.environ, {"JEV_WORKFLOW_DISABLED": "1"}):
            self.assertEqual(self.ask()["reason"], "disabled")

    def test_unapproved_project(self):
        self.cfg["authorized_projects"] = []; self.save()
        self.assertEqual(self.ask()["reason"], "project_not_authorized")
        self.assertFalse(self.calls)

    def test_missing_key(self):
        with patch.dict(os.environ, {"TYPESAFE_API_KEY": ""}):
            out = self.ask()
            self.assertEqual(out["status"], "FALLBACK")
            self.assertEqual(out["reason"], "missing_api_key")
        self.assertFalse(self.calls)

    def test_deterministic_skip(self):
        self.req["deterministic_available"] = True
        self.assertEqual(self.ask()["reason"], "use_deterministic_tools")

    def test_evidence_skip(self):
        self.req["evidence_sufficient"] = False
        self.assertEqual(self.ask()["reason"], "gather_evidence_first")

    def test_high_risk_skip(self):
        self.req["risk"] = "high"
        self.assertEqual(self.ask()["reason"], "high_risk_not_supported")
        self.assertFalse(self.calls)

    def test_unreviewed_data_skip(self):
        self.req["data_reviewed"] = False
        self.assertEqual(self.ask()["reason"], "data_not_reviewed")

    def test_email_blocks_entire_payload(self):
        self.req["questions"]["category"]["instructions"] += " See person@example.com"
        self.assertEqual(self.ask()["reason"], "possible_sensitive_data")
        self.assertFalse(self.calls)

    def test_actual_key_blocks_state(self):
        self.req["state"] += " unit-testing-credential"
        self.assertEqual(self.ask()["reason"], "possible_sensitive_data")

    def test_bearer_blocks_state(self):
        self.req["state"] += " Authorization: Bearer synthetic_1234567890"
        self.assertEqual(self.ask()["reason"], "possible_sensitive_data")

    def test_payload_size_includes_guard_instructions(self):
        self.cfg["max_payload_bytes"] = 512; self.save()
        self.req["state"] = "A" * 500
        self.assertEqual(self.ask()["reason"], "payload_too_large")

    def test_need_abstention(self):
        del self.req["questions"]["category"]["criteria"]["NEEDS_REVIEW"]
        self.assertEqual(self.ask()["reason"], "missing_abstention_choice")

    def test_no_truthy_string_bool(self):
        self.req["data_reviewed"] = "true"
        self.assertEqual(self.ask()["reason"], "invalid_boolean")

    def test_score_and_noul_valid(self):
        self.req["questions"] = {
            "relevance": {"type": "score", "instructions": "Rate topical relevance", "criteria": ["Unrelated", "Related"]},
            "mentions_cache": {"type": "noul", "instructions": "Does the evidence mention a cache?"},
        }
        out = self.ask()
        self.assertEqual(out["status"], "ADVISORY")
        self.assertNotIn("confidence", out["answers"]["mentions_cache"])

    def test_duplicate_skips_without_second_call(self):
        self.ask()
        self.assertEqual(self.ask()["reason"], "duplicate_request")
        self.assertEqual(len(self.calls), 1)

    def test_changed_payload_is_not_duplicate(self):
        self.ask()
        self.req["state"] += " Extra evidence."
        self.assertEqual(self.ask()["status"], "ADVISORY")
        self.assertEqual(len(self.calls), 2)

    def test_per_task_budget(self):
        for i in range(3):
            self.req["state"] += str(i)
            self.assertEqual(self.ask()["status"], "ADVISORY")
        self.req["state"] += "4"
        self.assertEqual(self.ask()["reason"], "task_budget_exhausted")
        self.assertEqual(len(self.calls), 3)

    def test_daily_budget_shared_across_tasks_and_projects(self):
        self.cfg["max_daily_calls"] = 1
        other = self.root / "other"
        other.mkdir()
        self.cfg["authorized_projects"].append(canonical_project(other))
        self.save()
        self.ask()
        task = self.flow.ledger.begin(canonical_project(other))
        self.assertEqual(self.ask(task=task, project=other)["reason"], "daily_budget_exhausted")
        self.assertEqual(len(self.calls), 1)

    def test_project_can_only_lower_limits(self):
        atomic_json(self.project / ".jev-workflow.json", {"max_task_calls": 1})
        self.ask()
        self.req["state"] += "other"
        self.assertEqual(self.ask()["reason"], "task_budget_exhausted")

    def test_project_cannot_authorize_itself(self):
        atomic_json(self.project / ".jev-workflow.json", {"authorized_projects": [str(self.project)]})
        self.assertEqual(self.ask()["reason"], "invalid_project_config")
        self.assertFalse(self.calls)

    def test_project_can_disable(self):
        atomic_json(self.project / ".jev-workflow.json", {"enabled": False})
        self.assertEqual(self.ask()["reason"], "disabled")

    def test_closed_task(self):
        self.flow.ledger.end(self.task, canonical_project(self.project))
        self.assertEqual(self.ask()["reason"], "closed_or_expired_task")

    def test_wrong_task_rejected(self):
        self.assertEqual(self.ask(task="not-a-created-task")["reason"], "unknown_or_wrong_project_task")

    def test_network_error_does_not_retry(self):
        self.flow.transport = lambda *a: {"ok": False, "reason": "timeout"}
        out = self.ask()
        self.assertEqual(out["status"], "FALLBACK")
        self.assertEqual(out["live_attempts"], 1)
        self.assertEqual(self.flow.ledger.stats()["attempts_with_unknown_usage"], 1)

    def test_failed_request_also_deduplicated(self):
        self.flow.transport = lambda *a: {"ok": False, "reason": "timeout"}
        self.ask()
        self.assertEqual(self.ask()["reason"], "duplicate_request")

    def test_401_never_retried(self):
        self.cfg["max_retries"] = 1; self.save()
        self.flow.transport = lambda *a: {"ok": False, "reason": "http_error", "http_status": 401}
        self.assertEqual(self.ask()["live_attempts"], 1)

    def test_opt_in_retry_counted(self):
        self.cfg["max_retries"] = 1; self.save()
        count = []
        def transport(payload, *args):
            count.append(1)
            return {"ok": False, "reason": "http_error", "http_status": 503, "retry_after_seconds": 0} if len(count) == 1 else valid_response(payload)
        self.flow.transport = transport
        with patch("jev_workflow.runner.time.sleep"):
            out = self.ask()
        self.assertEqual(out["status"], "ADVISORY")
        self.assertEqual(out["live_attempts"], 2)
        self.assertEqual(self.flow.ledger.stats()["reserved_live_attempts"], 2)

    def test_retry_cannot_bypass_task_budget(self):
        self.cfg.update(max_retries=1, max_task_calls=1); self.save()
        self.flow.transport = lambda *a: {"ok": False, "reason": "http_error", "http_status": 503, "retry_after_seconds": 0}
        with patch("jev_workflow.runner.time.sleep"):
            out = self.ask()
        self.assertEqual(out["live_attempts"], 1)
        self.assertEqual(out["reason"], "task_budget_exhausted")

    def test_long_retry_after_falls_back(self):
        self.cfg["max_retries"] = 1; self.save()
        self.flow.transport = lambda *a: {"ok": False, "reason": "http_error", "http_status": 429, "retry_after_seconds": 60}
        self.assertEqual(self.ask()["live_attempts"], 1)

    def test_invalid_response_falls_back(self):
        def transport(payload, *args):
            out = valid_response(payload)
            out["response"]["answers"]["category"]["choice"] = "EXECUTE_PAYMENT"
            return out
        self.flow.transport = transport
        out = self.ask()
        self.assertEqual(out["reason"], "invalid_response")
        self.assertFalse(out["authorization_granted"])
        self.assertEqual(out["answers"], {})

    def test_response_nan_rejected(self):
        def transport(payload, *args):
            out = valid_response(payload)
            out["response"]["answers"]["category"]["confidence"] = float("nan")
            return out
        self.flow.transport = transport
        self.assertEqual(self.ask()["reason"], "invalid_response")

    def test_missing_usage_is_not_invented(self):
        def transport(payload, *args):
            out = valid_response(payload)
            del out["response"]["usage"]
            return out
        self.flow.transport = transport
        self.assertEqual(self.ask()["reason"], "invalid_response")
        self.assertEqual(self.flow.ledger.stats()["attempts_with_unknown_usage"], 1)

    def test_model_version_mismatch(self):
        def transport(payload, *args):
            out = valid_response(payload)
            out["response"]["model"] = "jev-9.9.9"
            return out
        self.flow.transport = transport
        self.assertEqual(self.ask()["reason"], "model_mismatch")

    def test_logs_do_not_store_payload_or_key(self):
        self.req["state"] += " UNIQUE_PRIVATE_CONTENT_MARKER"
        self.ask()
        dump = "\n".join(self.flow.ledger.db.iterdump())
        self.assertNotIn("UNIQUE_PRIVATE_CONTENT_MARKER", dump)
        self.assertNotIn("unit-testing-credential", dump)
        self.assertNotIn(str(self.project), dump)
        self.assertNotIn('"probabilities"', dump)

    def test_usage_does_not_infer_codex(self):
        self.ask()
        stats = self.flow.ledger.stats()
        self.assertEqual(stats["reported_jev_input_tokens"], 100)
        self.assertIsNone(stats["codex_tokens"])
        self.assertIsNone(stats["codex_quota_savings"])

    def test_concurrent_reservation_cap(self):
        def reserve(i):
            ledger = Ledger(self.home)
            try:
                return ledger.reserve(self.task, canonical_project(self.project), f"input-{i}".encode(), "rank_candidates", 3, 30)
            except PolicyError:
                return None
            finally:
                ledger.close()
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(reserve, range(8)))
        self.assertEqual(sum(x is not None for x in results), 3)


class CLITests(unittest.TestCase):
    def test_isolated_demo(self):
        output = io.StringIO()
        with redirect_stdout(output):
            code = main(["demo"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue())["status"], "MOCK")

    def test_doctor_never_claims_live_verification(self):
        with tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()) as output:
            code = main(["--home", str(Path(d) / "state"), "doctor", "--project", d])
        self.assertEqual(code, 0)
        result = json.loads(output.getvalue())
        self.assertFalse(result["live_api_verified"])
        self.assertFalse(result["network_called"])

    def test_subprocess_timeout_is_bounded(self):
        with patch("jev_workflow.runner.subprocess.run", side_effect=subprocess.TimeoutExpired("worker", 10)) as run:
            result = call_worker(b"{}", "test-credential", 10)
        self.assertEqual(result["reason"], "timeout")
        self.assertNotIn("test-credential", str(run.call_args.args[0]))
        self.assertEqual(run.call_args.kwargs["timeout"], 10)

    def test_invalid_config_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            atomic_json(Path(d) / "config.json", {"mode": "MAGIC"})
            with self.assertRaises(PolicyError):
                load_config(Path(d))

if __name__ == "__main__":
    unittest.main()
