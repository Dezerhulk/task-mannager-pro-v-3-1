"""Export the FastAPI OpenAPI schema to a JSON file."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main_pro import app


OUTPUT_PATH = Path(__file__).resolve().parents[1] / "openapi.json"


if __name__ == "__main__":
    schema = app.openapi()
    OUTPUT_PATH.write_text(json.dumps(schema, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote OpenAPI schema to {OUTPUT_PATH}")
