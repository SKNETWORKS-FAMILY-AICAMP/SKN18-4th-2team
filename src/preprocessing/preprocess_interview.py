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
    """면접 응답 내 구어체 표현 및 특수문자 제거"""
    if not text:
        return ""
    text = re.sub(r"[^\w\s.,!?]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\b(어|음|아|그|저|이제|그러니까)\b", "", text)
    return text

# -----------------------------
# JSON → DataFrame 변환
# -----------------------------
def load_json_to_df(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = []

    for item in data:
        ds = item.get("dataSet", {})

        # 기본 텍스트
        q = clean_text(ds.get("question", {}).get("raw", {}).get("text", ""))
        a = clean_text(ds.get("answer", {}).get("raw", {}).get("text", ""))
        s = clean_text(ds.get("answer", {}).get("summary", {}).get("text", ""))

        # -----------------------------
        # metadata 구성
        # -----------------------------
        metadata = {}

        # (1) info 영역 복사
        metadata.update(ds.get("info", {}))  # occupation, gender, experience 등

        # (2) 데이터 관리 정보 (version, date 등)
        metadata["version"] = item.get("version", 1.0)
        metadata["date"] = item.get("date", "")

        # (3) 단어 수 통계
        metadata["question_wordCount"] = len(q.split()) if q else 0
        metadata["answer_wordCount"] = len(a.split()) if a else 0
        metadata["answer_summary_wordCount"] = len(s.split()) if s else 0

        # (4) 질문/답변의 intent·emotion 원본 구조 그대로 유지
        metadata["question_intent"] = ds.get("question", {}).get("intent", [])
        metadata["answer_intent"] = ds.get("answer", {}).get("intent", [])
        metadata["question_emotion"] = ds.get("question", {}).get("emotion", [])
        metadata["answer_emotion"] = ds.get("answer", {}).get("emotion", [])

        # (5) intent / emotion의 대표 카테고리 (첫 번째 항목)
        try:
            metadata["answer_intent_category"] = metadata["answer_intent"][0].get("category", "")
        except Exception:
            metadata["answer_intent_category"] = ""
        try:
            metadata["answer_emotion_category"] = metadata["answer_emotion"][0].get("category", "")
        except Exception:
            metadata["answer_emotion_category"] = ""

        # (6) 메타데이터 JSON 문자열화
        metadata_json = json.dumps(metadata, ensure_ascii=False)

        # -----------------------------
        # Row 구성
        # -----------------------------
        rows.append({
            "question": q,
            "answer": a,
            "summary": s,
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
    process_file("train_merged_all.json", "processed_train.csv")
    process_file("valid_merged_all.json", "processed_valid.csv")

if __name__ == "__main__":
    main()
