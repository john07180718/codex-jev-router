"""Local user policy. Repository policy may only restrict it."""
from __future__ import annotations
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

MODEL_RE = re.compile(r"jev-(?:latest|preview|[0-9]+\.[0-9]+\.[0-9]+)\Z")
DEFAULTS: dict[str, Any] = {
    "schema_version": 1, "mode": "mock", "model": "jev-1.13.0",
    "max_task_calls": 3, "max_daily_calls": 30,
    "max_payload_bytes": 16000, "timeout_seconds": 10,
    "max_retries": 0, "authorized_projects": [],
}

class PolicyError(ValueError):
    """A safe, constant error code; never include submitted content."""

def workflow_home(explicit: str | None = None) -> Path:
    return Path(explicit).expanduser().resolve() if explicit else Path.home() / ".codex-jev-workflow"

def canonical_project(path: str | Path) -> str:
    root = Path(path).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise PolicyError("invalid_project")
    return os.path.normcase(str(root))

def read_json(path: Path, limit: int = 65536) -> Any:
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise PolicyError("file_too_large")
    try:
        return json.loads(data.decode("utf-8-sig"), parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, UnicodeError):
        raise PolicyError("invalid_json") from None

def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(prefix=".jev-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)

def load_config(home: Path) -> dict[str, Any]:
    path = home / "config.json"
    cfg = dict(DEFAULTS)
    cfg["authorized_projects"] = []
    if path.exists():
        raw = read_json(path)
        if not isinstance(raw, dict) or set(raw) - set(DEFAULTS):
            raise PolicyError("invalid_user_config")
        cfg.update(raw)
    if type(cfg["schema_version"]) is not int or cfg["schema_version"] != 1:
        raise PolicyError("unsupported_config_version")
    if cfg["mode"] not in ("off", "mock", "live"):
        raise PolicyError("invalid_mode")
    if not isinstance(cfg["model"], str) or not MODEL_RE.fullmatch(cfg["model"]):
        raise PolicyError("invalid_model")
    ranges = {"max_task_calls": (0, 20), "max_daily_calls": (0, 1000),
              "max_payload_bytes": (512, 64000), "timeout_seconds": (1, 30), "max_retries": (0, 1)}
    for key, (lo, hi) in ranges.items():
        if type(cfg[key]) is not int or not lo <= cfg[key] <= hi:
            raise PolicyError("invalid_limit")
    if not isinstance(cfg["authorized_projects"], list) or not all(isinstance(p, str) and Path(p).is_absolute() for p in cfg["authorized_projects"]):
        raise PolicyError("invalid_project_authorizations")
    return cfg

def effective_config(home: Path, project: str) -> dict[str, Any]:
    cfg = load_config(home)
    cfg["enabled"] = os.environ.get("JEV_WORKFLOW_DISABLED") != "1"
    local = Path(project) / ".jev-workflow.json"
    if local.exists():
        raw = read_json(local, 4096)
        if not isinstance(raw, dict) or set(raw) - {"enabled", "max_task_calls", "max_payload_bytes"}:
            raise PolicyError("invalid_project_config")
        if "enabled" in raw:
            if type(raw["enabled"]) is not bool:
                raise PolicyError("invalid_project_config")
            cfg["enabled"] = cfg["enabled"] and raw["enabled"]
        for key in ("max_task_calls", "max_payload_bytes"):
            if key in raw:
                if type(raw[key]) is not int or raw[key] < 0:
                    raise PolicyError("invalid_project_config")
                cfg[key] = min(cfg[key], raw[key])
    return cfg
