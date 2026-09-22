"""Preview-first installer/uninstaller; backs up existing content and preserves unrelated rules."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BEGIN = "<!-- CODEX_JEV_WORKFLOW:BEGIN -->"
END = "<!-- CODEX_JEV_WORKFLOW:END -->"
MANIFEST = ".jev-workflow-install.json"


def edit_block(original: str, block: str | None) -> str:
    if original.count(BEGIN) != original.count(END) or original.count(BEGIN) > 1:
        raise ValueError("Malformed managed block; inspect manually")
    if BEGIN in original:
        start = original.index(BEGIN)
        finish = original.index(END) + len(END)
        if finish < start:
            raise ValueError("Malformed managed block")
        return original[:start] + (block or "") + original[finish:]
    if block is None:
        return original
    separator = "\n\n" if original and not original.endswith("\n\n") else ""
    return original + separator + block + "\n"


def tree_hashes(path: Path) -> dict[str, str]:
    return {p.relative_to(path).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in path.rglob("*") if p.is_file() and p.name != MANIFEST and "__pycache__" not in p.parts and p.suffix != ".pyc"}


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=("user", "project"), default="user")
    parser.add_argument("--project", default=".")
    parser.add_argument("--global-rule", action="store_true", help="Also merge a short global block; user scope only")
    parser.add_argument("--apply", action="store_true", help="Without this flag, only print a plan")
    parser.add_argument("--uninstall", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.global_rule and args.scope != "user":
            raise ValueError("Global rules require user scope")
        base = Path.home() if args.scope == "user" else Path(args.project).expanduser().resolve(strict=True)
        target = base / ".agents" / "skills" / "jev-assist"
        codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser().resolve()
        rule = None
        new_text = None
        manifest_data = None
        if target.is_symlink():
            raise ValueError("Refusing to overwrite/remove a symlinked skill")
        if target.exists():
            if not (target / MANIFEST).is_file():
                raise ValueError("An unmanaged jev-assist skill exists; inspect it before installing")
            manifest_data = json.loads((target / MANIFEST).read_text(encoding="utf-8"))
            if tree_hashes(target) != manifest_data.get("files"):
                raise ValueError("Installed skill was modified; preserve/reconcile changes before reinstall/uninstall")
        if args.uninstall and manifest_data and manifest_data.get("global_rule"):
            rule = Path(manifest_data["global_rule"])
        elif args.global_rule:
            override = codex_home / "AGENTS.override.md"
            rule = override if override.exists() and override.read_text(encoding="utf-8").strip() else codex_home / "AGENTS.md"
        if rule:
            if rule.is_symlink():
                raise ValueError("Refusing to rewrite a symlinked global instruction file")
            original = rule.read_text(encoding="utf-8") if rule.exists() else ""
            block = None if args.uninstall else BEGIN + "\n" + (ROOT / "skills" / "global-rule.md").read_text(encoding="utf-8").strip() + "\n" + END
            new_text = edit_block(original, block)
        print(json.dumps({"operation": "uninstall" if args.uninstall else "install",
                          "apply": args.apply, "skill_directory": str(target),
                          "global_rule_file": str(rule) if rule else None,
                          "network_called": False}, indent=2))
        if not args.apply:
            return 0
        backup = Path.home() / ".codex-jev-workflow" / "install-backups" / uuid.uuid4().hex
        backup.mkdir(parents=True, exist_ok=True)
        if rule and rule.exists() and new_text != rule.read_text(encoding="utf-8"):
            shutil.copy2(rule, backup / rule.name)
        if target.exists():
            shutil.copytree(target, backup / "jev-assist", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        if args.uninstall:
            if rule and new_text is not None:
                rule.write_text(new_text, encoding="utf-8")
            if target.exists():
                shutil.rmtree(target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            stage = Path(tempfile.mkdtemp(prefix=".jev-stage-", dir=target.parent))
            try:
                shutil.copytree(ROOT / "skills" / "jev-assist", stage, dirs_exist_ok=True)
                shutil.copytree(ROOT / "jev_workflow", stage / "scripts" / "jev_workflow",
                                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
                # Preserve the tracked global block on an upgrade even without --global-rule.
                tracked_rule = str(rule) if rule else (manifest_data or {}).get("global_rule")
                (stage / MANIFEST).write_text(json.dumps({"version": "0.1.0", "global_rule": tracked_rule,
                                                         "files": tree_hashes(stage)}, indent=2), encoding="utf-8")
                if target.exists():
                    shutil.rmtree(target)
                stage.rename(target)
                if rule and new_text is not None:
                    rule.parent.mkdir(parents=True, exist_ok=True)
                    rule.write_text(new_text, encoding="utf-8")
            finally:
                if stage.exists():
                    shutil.rmtree(stage)
        print(json.dumps({"completed": True, "backup_directory": str(backup),
                          "note": "Not a live API test. Restart Codex to verify rule/skill discovery."}))
        return 0
    except (OSError, ValueError, KeyError, TypeError):
        print(json.dumps({"completed": False, "reason": "install_conflict_or_local_error",
                          "note": "No remote changes. Inspect local files and backups; do not overwrite blindly."}))
        return 2

if __name__ == "__main__":
    raise SystemExit(run())
