"""Human-operated launcher: enter a key privately and pass it to one child process.

Never invoke this from an unattended coding agent. No key is written to disk.
This is process-environment delivery, not isolation from the same OS user.
"""
from __future__ import annotations
import getpass
import os
import shutil
import subprocess
import sys

def main() -> int:
    command = sys.argv[1:]
    if not command:
        print("Usage: python tools/with_key.py codex [arguments]")
        return 2
    if not sys.stdin.isatty():
        print("Run this in your own interactive terminal, not an agent tool call.")
        return 2
    key = getpass.getpass("TYPESAFE_API_KEY (hidden; not saved): ")
    if not key:
        print("No key provided. Nothing launched.")
        return 2
    env = dict(os.environ)
    env["TYPESAFE_API_KEY"] = key
    command[0] = shutil.which(command[0]) or command[0]
    try:
        return subprocess.run(command, env=env, check=False).returncode
    except OSError:
        print("Could not start the requested program. Check its installation/path.")
        return 2
    finally:
        env.pop("TYPESAFE_API_KEY", None)
        key = ""

if __name__ == "__main__":
    raise SystemExit(main())
