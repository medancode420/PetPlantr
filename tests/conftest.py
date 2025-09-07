import os
import sys
from pathlib import Path

# Ensure tests don't require real model by default
os.environ.setdefault("ENABLE_BREED_API", "true")

# Add repo root to sys.path so `src` package is importable
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
	sys.path.insert(0, str(ROOT))
