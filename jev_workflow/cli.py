"""Small, JSON-output CLI. Running doctor/stats does not contact the provider."""
from __future__ import annotations
import argparse
import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path
from typing import Any
from . import __version__
from .config import (PolicyError, atomic_json, canonical_project, effective_config,
                     load_config, read_json, workflow_home)
from .ledger import Ledger
from .runner import Workflow


def emit(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=True, allow_nan=False, indent=2))

def demo_request() -> dict[str, Any]:
    return {
        "purpose": "classify_test_failures", "risk": "low",
        "deterministic_available": False, "evidence_sufficient": True,
        "expected_benefit": "batch_semantic_labels", "data_reviewed": True,
        "state": "Synthetic evidence: test_cache reports a stale value after invalidation. No actual project or customer data.",
        "questions": {"category": {"type": "choice", "instructions": "Classify the reported symptom, not its unproven root cause.",
          "criteria": {"CACHE_STATE": "Stale cache state", "NETWORK": "Network connection symptom",
                       "NEEDS_REVIEW": "Insufficient evidence or another category"}}},
    }

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Optional, advisory-only Codex + JEV development workflow")
    parser.add_argument("--home", help="Local state directory; omit normally. Changing it creates separate budgets.")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="Create a local mock-only config, never overwrite existing config")
    configure = sub.add_parser("configure", help="User operation: select mode; does not authorize projects")
    configure.add_argument("--mode", choices=("off", "mock", "live"), required=True)
    authorize = sub.add_parser("authorize", help="User operation: allow sanitized development excerpts from exactly this project")
    authorize.add_argument("--project", required=True)
    authorize.add_argument("--allow-external-data", action="store_true", required=True)
    revoke = sub.add_parser("revoke", help="User operation: revoke a project's data authorization")
    revoke.add_argument("--project", required=True)
    doctor = sub.add_parser("doctor", help="Local preflight only, NOT API connectivity validation")
    doctor.add_argument("--project", default=".")
    begin = sub.add_parser("begin", help="Create one shared task id for this user task and all its subagents")
    begin.add_argument("--project", default=".")
    end = sub.add_parser("end", help="Close a task; keep usage metadata")
    end.add_argument("--project", default=".")
    end.add_argument("--task", required=True)
    ask = sub.add_parser("ask", help="Validate/route one narrow request, read JSON from file or stdin")
    ask.add_argument("--project", default=".")
    ask.add_argument("--task", required=True)
    ask.add_argument("--request", default="-", help="JSON request path, or - for stdin")
    sub.add_parser("stats", help="Local measured JEV usage; never invent Codex usage")
    sub.add_parser("demo", help="Isolated mock demo; no network, no credentials, no personal config changes")
    args = parser.parse_args(argv)
    ledger = None
    flow = None
    try:
        home = workflow_home(args.home)
        if args.command == "demo":
            with tempfile.TemporaryDirectory(prefix="jev-demo-") as directory:
                root = Path(directory)
                flow = Workflow(root / "local-state")
                task = flow.ledger.begin(canonical_project(root))
                result = flow.ask(str(root), task, demo_request())
                emit(result)
                flow.close()
                flow = None
                return 0 if result["status"] == "MOCK" else 2
        if args.command == "init":
            cfg = load_config(home)
            if not (home / "config.json").exists():
                atomic_json(home / "config.json", cfg)
            emit({"config": str(home / "config.json"), "mode": cfg["mode"], "network_called": False})
        elif args.command in ("configure", "authorize", "revoke"):
            cfg = load_config(home)
            if args.command == "configure":
                cfg["mode"] = args.mode
            else:
                root = canonical_project(args.project)
                projects = set(cfg["authorized_projects"])
                projects.add(root) if args.command == "authorize" else projects.discard(root)
                cfg["authorized_projects"] = sorted(projects)
            atomic_json(home / "config.json", cfg)
            emit({"updated": True, "mode": cfg["mode"], "authorized_project_count": len(cfg["authorized_projects"]), "network_called": False})
        elif args.command == "doctor":
            root = canonical_project(args.project)
            cfg = effective_config(home, root)
            ready = cfg["mode"] == "live" and cfg["enabled"] and root in cfg["authorized_projects"] and bool(os.environ.get("TYPESAFE_API_KEY"))
            emit({"version": __version__, "mode": cfg["mode"], "enabled": cfg["enabled"], "model": cfg["model"],
                  "project_authorized": root in cfg["authorized_projects"], "api_key_present": bool(os.environ.get("TYPESAFE_API_KEY")),
                  "local_prerequisites_met": ready, "live_api_verified": False,
                  "network_called": False, "task_call_cap": cfg["max_task_calls"], "daily_call_cap_utc": cfg["max_daily_calls"]})
        elif args.command == "ask":
            if args.request == "-":
                data = sys.stdin.buffer.read(65537)
                if len(data) > 65536:
                    raise PolicyError("file_too_large")
                request = json.loads(data.decode("utf-8-sig"))
            else:
                request = read_json(Path(args.request))
            flow = Workflow(home)
            result = flow.ask(args.project, args.task, request)
            emit(result)
            # Skip/fallback are valid advisory workflow outcomes, not successful model calls.
        else:
            ledger = Ledger(home)
            if args.command == "stats":
                emit(ledger.stats())
            elif args.command == "begin":
                task = ledger.begin(canonical_project(args.project))
                emit({"task_id": task, "expires_in_hours": 24, "network_called": False})
            elif args.command == "end":
                ledger.end(args.task, canonical_project(args.project))
                emit({"closed": True, "network_called": False})
        return 0
    except PolicyError as exc:
        emit({"status": "ERROR", "reason": str(exc), "authorization_granted": False})
        return 2
    except (OSError, ValueError, TypeError, sqlite3.Error, RecursionError):
        emit({"status": "ERROR", "reason": "local_operation_failed", "authorization_granted": False})
        return 2
    finally:
        if ledger is not None:
            ledger.close()
        if flow is not None:
            flow.close()

if __name__ == "__main__":
    raise SystemExit(main())
