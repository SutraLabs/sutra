"""Legacy entrypoint moved from repo root; kept here for backward compatibility."""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sutra.cli import main


if __name__ == "__main__":
    main()
