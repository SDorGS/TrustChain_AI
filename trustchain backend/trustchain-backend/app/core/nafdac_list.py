import json
from pathlib import Path

NAFDAC_FILE = Path(__file__).resolve().parents[2] / "nafdac_products.json"

VALID_NAFDAC = set()

if NAFDAC_FILE.exists():
    try:
        with NAFDAC_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    code = str(item.get("nafdac_no", "")).strip().upper()
                    if code:
                        VALID_NAFDAC.add(code)
                elif isinstance(item, str):
                    code = item.strip().upper()
                    if code:
                        VALID_NAFDAC.add(code)
    except Exception:
        VALID_NAFDAC = set()