"""Installed launcher; package is copied next to this file by tools/install.py."""
from pathlib import Path
import sys

here = Path(__file__).resolve()
if not (here.parent / "jev_workflow").is_dir():
    # Development checkout; installed copies use the adjacent package instead.
    sys.path.insert(0, str(here.parents[3]))
from jev_workflow.cli import main
raise SystemExit(main())
