
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

INPUT_FILE = Path("data/processed/mandi_prices_clean.csv")
OUTPUT_FILE = Path("data/processed/import_metadata.json")


def create_import_metadata():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    content = INPUT_FILE.read_bytes()
    batch_id = hashlib.sha256(content).hexdigest()

    metadata = {
        "source_name": "AGMARKNET",
        "source_url": (
            "https://api.agmarknet.gov.in/"
            "v1/prices-and-arrivals/date-wise/specific-commodity"
        ),
        "retrieved_at": None,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "batch_id": batch_id,
        "input_file": str(INPUT_FILE),
        "record_count": sum(1 for _ in INPUT_FILE.open()) - 1,
        "source_status": "UNVERIFIED",
        "notes": (
            "The API request returned TOKEN_OR_CAPTCHA_REQUIRED. "
            "The file's official origin has not been independently verified."
        ),
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )

    print("Import metadata saved to:", OUTPUT_FILE)
    print("Batch ID:", batch_id)
    print("Source status:", metadata["source_status"])


if __name__ == "__main__":
    create_import_metadata()
