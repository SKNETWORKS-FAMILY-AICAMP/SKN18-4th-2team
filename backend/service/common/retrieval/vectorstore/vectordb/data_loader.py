import csv
from pathlib import Path
from typing import Any, Dict, List

SERVICE_DIR = Path(__file__).resolve().parents[4]
DATABASE_DIR = SERVICE_DIR / "database" / "college"

CHUNK_CSV_PATH = DATABASE_DIR / "majors_with_chunks.csv"
UNIV_CSV_PATH = DATABASE_DIR / "major_universities.csv"


def _ensure_path(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"{path} 파일을 찾을 수 없습니다. export_to_csv.py 결과를 확인하세요.")
    return path


def load_chunk_rows(csv_path: Path | None = None) -> List[Dict[str, Any]]:
    """Return flattened chunk rows (metadata + chunk_text) from CSV export."""
    path = _ensure_path(Path(csv_path) if csv_path else CHUNK_CSV_PATH)
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def load_university_rows(csv_path: Path | None = None) -> List[Dict[str, Any]]:
    """Return major-university mapping rows from CSV export."""
    path = _ensure_path(Path(csv_path) if csv_path else UNIV_CSV_PATH)
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def iter_batches(rows: List[Dict[str, Any]], batch_size: int):
    """Yield successive slices of `rows` with `batch_size` length."""
    for start in range(0, len(rows), batch_size):
        yield rows[start : start + batch_size]
