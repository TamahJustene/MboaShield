import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
VERSION = "0.2.0"
DB_PATH = Path(os.getenv("MBOASHIELD_DB_PATH", ROOT / "storage" / "mboashield.db"))
