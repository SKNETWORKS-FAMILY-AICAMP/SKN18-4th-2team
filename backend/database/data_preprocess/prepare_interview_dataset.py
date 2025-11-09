from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
RAW_CSV = BASE_DIR / "valid_merged_all.csv"
OUTPUT_DIR = BASE_DIR.parent / "interview"
OUTPUT_CSV = OUTPUT_DIR / "valid_merged_all_preprocessed.csv"

JSON_FIELDS = [
    "question_emotion",
    "question_intent",
    "answer_emotion",
    "answer_intent",
]


def safe_json_load(value: Any):
    """Parse JSON strings stored inside the CSV; return [] when empty/invalid."""

    if pd.isna(value):
        return []

    text = str(value).strip()
    if not text or text == "[]":
        return []

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # leave as plain string for debugging purposes
        return text


def build_metadata(row: pd.Series) -> Dict[str, Any]:
    """Collect the fields we want to carry as metadata."""

    metadata = {
        "version": row.get("version"),
        "date": row.get("date"),
        "occupation": row.get("occupation"),
        "channel": row.get("channel"),
        "place": row.get("place"),
        "gender": row.get("gender"),
        "ageRange": row.get("ageRange"),
        "experience": row.get("experience"),
        "question_wordCount": row.get("question_wordCount"),
        "answer_wordCount": row.get("answer_wordCount"),
        "answer_summary_wordCount": row.get("answer_summary_wordCount"),
        "question_intent": safe_json_load(row.get("question_intent")),
        "answer_intent": safe_json_load(row.get("answer_intent")),
        "answer_intent_text": row.get("answer_intent_text"),
        "answer_intent_expression": row.get("answer_intent_expression"),
        "answer_intent_category": row.get("answer_intent_category"),
        "question_emotion": safe_json_load(row.get("question_emotion")),
        "answer_emotion": safe_json_load(row.get("answer_emotion")),
    }

    return metadata


def process() -> None:
    if not RAW_CSV.exists():
        raise FileNotFoundError(f"Raw CSV not found: {RAW_CSV}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(RAW_CSV)

    records = []
    for _, row in df.iterrows():
        metadata = build_metadata(row)
        record = {
            "question": (row.get("question_text") or "").strip(),
            "answer": (row.get("answer_text") or "").strip(),
            "answer_summary": (row.get("answer_summary") or "").strip(),
            "metadata": json.dumps(metadata, ensure_ascii=False),
        }
        records.append(record)

    output_df = pd.DataFrame(records)
    output_df.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved {len(output_df)} rows to {OUTPUT_CSV}")


if __name__ == "__main__":
    process()
