import json
import re
import pandas as pd
from pathlib import Path

# -----------------------------
# 경로 설정
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------
# 텍스트 정제 함수
# -----------------------------
def clean_text(text):
    """텍스트 내 HTML 태그, 특수문자, 여백 제거"""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)  # HTML 태그 제거
    text = re.sub(r"[^\w\s.,!?]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# -----------------------------
# JSON → DataFrame 변환
# -----------------------------
def load_json_to_df(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = []

    for item in data:
        summary = clean_text(item.get("summary", ""))
        interest = clean_text(item.get("interest", ""))
        property_ = clean_text(item.get("property", ""))

        # -----------------------------
        # metadata 구성
        # -----------------------------
        metadata = {
            "majorSeq": item.get("majorSeq", ""),
            "major": item.get("major", ""),
            "salary": item.get("salary", ""),
            "employment": clean_text(item.get("employment", "")),
            "job": clean_text(item.get("job", "")),
            "qualifications": clean_text(item.get("qualifications", "")),
            "universities": item.get("universities", [])
        }

        metadata_json = json.dumps(metadata, ensure_ascii=False)

        rows.append({
            "summary": summary,
            "interest": interest,
            "property": property_,
            "metadata": metadata_json
        })

    return pd.DataFrame(rows)

# -----------------------------
# 파일별 전처리 실행
# -----------------------------
def process_file(file_name, output_name):
    file_path = DATA_DIR / file_name
    df = load_json_to_df(file_path)
    output_path = OUTPUT_DIR / output_name
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"✅ {file_name} → {output_path} 저장 완료! (총 {len(df)}개)")

# -----------------------------
# 메인 실행
# -----------------------------
def main():
    process_file("major_details_공학.json", "processed_engineering.csv")
    process_file("major_details_의약.json", "processed_medical.csv")
    process_file("major_details_자연.json", "processed_science.csv")

if __name__ == "__main__":
    main()
