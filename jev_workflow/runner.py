"""Advisory-only workflow. Does not modify a project or execute model output."""
from __future__ import annotations
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable
from .config import PolicyError, effective_config, canonical_project
from .ledger import Ledger
from .privacy import sensitive
from .schema import encoded, make_payload, mock_response, validate_request, validate_response

Transport = Callable[[bytes, str, int], dict[str, Any]]

def call_worker(payload: bytes, key: str, timeout: int) -> dict[str, Any]:
    # Avoid injecting source code into a shell. Keep credentials off argv/stdout.
    env = {k: v for k, v in os.environ.items() if k in ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "HOME", "USERPROFILE", "SSL_CERT_FILE", "SSL_CERT_DIR")}
    env["TYPESAFE_API_KEY"] = key
    try:
        proc = subprocess.run([sys.executable, "-I", str(Path(__file__).with_name("transport.py"))],
                              input=payload, capture_output=True, timeout=timeout, env=env, check=False)
    except subprocess.TimeoutExpired:
        return {"ok": False, "reason": "timeout"}
    except OSError:
        return {"ok": False, "reason": "worker_unavailable"}
    if proc.returncode != 0 or len(proc.stdout) > 524288:
        return {"ok": False, "reason": "worker_error"}
    try:
        raw = json.loads(proc.stdout)
        if not isinstance(raw, dict) or type(raw.get("ok")) is not bool:
            raise ValueError()
        return raw
    except (ValueError, UnicodeError):
        return {"ok": False, "reason": "worker_error"}

class Workflow:
    def __init__(self, home: Path, transport: Transport = call_worker):
        self.home = home
        self.ledger = Ledger(home)
        self.transport = transport

    def close(self) -> None:
        self.ledger.close()

    def ask(self, project: str, task: str, request: Any) -> dict[str, Any]:
        start = time.monotonic()
        attempts = 0
        mode = "unknown"
        purpose = "invalid"
        root = "unresolved"

        def result(status: str, reason: str, **extra: Any) -> dict[str, Any]:
            elapsed = round((time.monotonic() - start) * 1000)
            self.ledger.event(task, root, purpose, mode, status, reason, attempts, elapsed)
            return {"status": status, "reason": reason, "advisory_only": True,
                    "authorization_granted": False, "live_attempts": attempts,
                    "elapsed_ms": elapsed, "answers": {}, "jev_usage": None,
                    "codex_usage": None, **extra}

        try:
            root = canonical_project(project)
            cfg = effective_config(self.home, root)
            mode = cfg["mode"]
            self.ledger.check_task(task, root)
            if not cfg["enabled"] or mode == "off":
                return result("SKIP", "disabled")
            validate_request(request)
            purpose = request["purpose"]
            if request["risk"] == "high":
                return result("SKIP", "high_risk_not_supported")
            if request["deterministic_available"]:
                return result("SKIP", "use_deterministic_tools")
            if not request["evidence_sufficient"]:
                return result("SKIP", "gather_evidence_first")
            if not request["data_reviewed"]:
                return result("SKIP", "data_not_reviewed")
            payload = make_payload(request, cfg["model"])
            data = encoded(payload)
            if len(data) > cfg["max_payload_bytes"]:
                return result("SKIP", "payload_too_large")
            key = os.environ.get("TYPESAFE_API_KEY", "")
            if sensitive(data, key):
                return result("SKIP", "possible_sensitive_data")
            if mode == "mock":
                return result("MOCK", "simulation_only_not_inference", answers=mock_response(request["questions"]))
            if root not in cfg["authorized_projects"]:
                return result("SKIP", "project_not_authorized")
            if not key:
                return result("FALLBACK", "missing_api_key")
            for attempt_no in range(cfg["max_retries"] + 1):
                reservation = self.ledger.reserve(task, root, data, purpose, cfg["max_task_calls"], cfg["max_daily_calls"], retry=attempt_no > 0)
                attempts += 1
                try:
                    reply = self.transport(data, key, cfg["timeout_seconds"])
                except Exception:
                    self.ledger.finish(reservation, "transport_exception")
                    return result("FALLBACK", "transport_exception")
                if not isinstance(reply, dict):
                    self.ledger.finish(reservation, "invalid_transport_reply")
                    return result("FALLBACK", "invalid_transport_reply")
                if reply.get("ok") is True:
                    try:
                        parsed = validate_response(reply.get("response"), request["questions"])
                    except (PolicyError, TypeError, KeyError) as exc:
                        self.ledger.finish(reservation, "invalid_response")
                        return result("FALLBACK", "invalid_response")
                    # Pinned versions must not silently switch.
                    if cfg["model"] not in ("jev-latest", "jev-preview") and parsed["model"] != cfg["model"]:
                        self.ledger.finish(reservation, "model_mismatch", parsed)
                        return result("FALLBACK", "model_mismatch")
                    self.ledger.finish(reservation, "ok", parsed)
                    return result("ADVISORY", "verify_before_use", answers=parsed["answers"], model=parsed["model"], jev_usage=parsed["usage"])
                http_status = reply.get("http_status")
                reason = f"http_{http_status}" if type(http_status) is int and 100 <= http_status <= 599 else reply.get("reason")
                safe_reasons = {"timeout", "network_error", "worker_unavailable", "worker_error", "response_too_large", "invalid_response_json", "invalid_transport_input"}
                if not (isinstance(reason, str) and (reason in safe_reasons or reason.startswith("http_") and reason[5:].isdigit())):
                    reason = "transport_error"
                self.ledger.finish(reservation, reason)
                delay = reply.get("retry_after_seconds")
                if delay is None:
                    delay = 1.0
                retryable = type(http_status) is int and http_status in (429, 503, 529)
                if not retryable or attempt_no >= cfg["max_retries"] or type(delay) not in (int, float) or not 0 <= delay <= 2:
                    return result("FALLBACK", reason)
                time.sleep(max(0.1, delay))
            return result("FALLBACK", "no_result")
        except PolicyError as exc:
            return result("SKIP", str(exc))
        except (OSError, TypeError, KeyError, ValueError, RecursionError):
            return result("FALLBACK", "local_validation_error")
