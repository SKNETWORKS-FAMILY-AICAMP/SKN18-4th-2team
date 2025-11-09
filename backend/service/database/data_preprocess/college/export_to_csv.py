import csv
import json
from pathlib import Path
from typing import Iterable, List, Dict


BASE_DIR = Path(__file__).resolve().parent  # data_preprocess directory
OUTPUT_FILE = BASE_DIR.parent / "college" / "majors_with_chunks.csv"
UNIV_OUTPUT_FILE = BASE_DIR.parent / "college" / "major_universities.csv"
CHUNK_FIELDS = ("summary", "interest", "property")
METADATA_FIELDS = (
    "majorSeq",
    "major",
    "salary",
    "employment",
    "job",
    "qualifications",
)


def load_json_records() -> Iterable[Dict[str, str]]:
    """Yield every major entry from all JSON files in this directory."""
    json_files: List[Path] = sorted(BASE_DIR.glob("major_details_*.json"))
    for path in json_files:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, list):
            raise ValueError(f"{path.name} does not contain a list of records.")
        for item in data:
            yield item


def export_csv() -> None:
    """Create majors_with_chunks.csv next to the JSON sources."""
    output_fields = [*METADATA_FIELDS, "chunk_field", "chunk_text"]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as chunks_file, UNIV_OUTPUT_FILE.open(
        "w", encoding="utf-8", newline=""
    ) as univ_file:
        chunk_writer = csv.DictWriter(chunks_file, fieldnames=output_fields)
        chunk_writer.writeheader()

        univ_writer = csv.DictWriter(
            univ_file,
            fieldnames=["majorSeq", "schoolName", "majorName"],
        )
        univ_writer.writeheader()

        for record in load_json_records():
            metadata = {field: record.get(field, "") for field in METADATA_FIELDS}

            for chunk_field in CHUNK_FIELDS:
                chunk_text = record.get(chunk_field, "")
                if not chunk_text:
                    continue
                row = {
                    **metadata,
                    "chunk_field": chunk_field,
                    "chunk_text": chunk_text,
                }
                chunk_writer.writerow(row)

            for uni in record.get("universities", []) or []:
                univ_writer.writerow(
                    {
                        "majorSeq": record.get("majorSeq", ""),
                        "schoolName": uni.get("schoolName", ""),
                        "majorName": uni.get("majorName", ""),
                    }
                )


if __name__ == "__main__":
    export_csv()
