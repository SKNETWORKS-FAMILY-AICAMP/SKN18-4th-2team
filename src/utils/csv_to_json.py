import pandas as pd
import json
from pathlib import Path

base_dir = Path("data")
csv_base = base_dir / "processed"
json_base = base_dir / "json"

# 폴더 없으면 자동 생성
json_base.mkdir(parents=True, exist_ok=True)

for csv_path in csv_base.rglob("*.csv"):
    df = pd.read_csv(csv_path)
    subdir = csv_path.parent.relative_to(csv_base)
    output_dir = json_base / subdir
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset_type = (subdir.name + csv_path.name).lower()
    records = []

    for _, row in df.iterrows():
        # ✅ 채용 면접 데이터
        if "interview" in dataset_type or "train" in dataset_type or "valid" in dataset_type:
            content = str(row.get("question") or row.get("질문") or row.get("Q") or row.get("summary") or "")
            metadata = {
                "id": int(row.get("id", row.get("번호", 0))) if ("id" in df.columns or "번호" in df.columns) else None,
                "answer": row.get("answer") or row.get("답변") or row.get("A") or "",
                "summary": row.get("summary") or row.get("요약") or "",
                "category": row.get("category") or row.get("유형") or "",
                "job_field": row.get("job_field") or row.get("직무") or "",
                "company": row.get("company") or row.get("회사") or "",
                "difficulty": row.get("difficulty") or row.get("난이도") or "",
                "source": csv_path.name
            }

        # ✅ 대학/학과 데이터
        elif any(x in dataset_type for x in ["college", "university", "engineering", "medical", "science"]):
            content = str(row.get("summary") or row.get("요약") or "")
            metadata = {
                "id": int(row.get("id", row.get("번호", 0))) if ("id" in df.columns or "번호" in df.columns) else None,
                "interest": row.get("interest") or row.get("관심분야") or row.get("흥미") or "",
                "property": row.get("property") or row.get("특징") or row.get("성격") or "",
                "source": csv_path.name
            }

        # ✅ 기타 fallback
        else:
            first_col = df.columns[0]
            content = str(row[first_col])
            metadata = {"source": csv_path.name}

        # ❗빈 필드는 자동 제거
        metadata = {k: v for k, v in metadata.items() if v not in [None, ""]}

        record = {"content": content, "metadata": metadata}
        records.append(record)

    json_path = output_dir / f"{csv_path.stem}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"✅ {json_path} 생성 완료 ({len(records)}개 레코드)")
