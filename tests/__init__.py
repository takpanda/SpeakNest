import sys
from pathlib import Path

# Make ``src/`` importable when run directly from the repo root.
src = Path(__file__).resolve().parent.parent / "src"
if src.exists() and str(src) not in sys.path:
    sys.path.insert(0, str(src))
