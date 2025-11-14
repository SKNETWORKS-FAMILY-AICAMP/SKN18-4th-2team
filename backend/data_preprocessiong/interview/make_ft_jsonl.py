import os
import json
from pathlib import Path
import pandas as pd


# 경로 설정: 현재 파일 기준 프로젝트 루트 추정
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASE_DIR = PROJECT_ROOT / "data" / "interview"
INPUT_CSV = BASE_DIR / "interview_final_db.csv"
OUTPUT_JSONL = BASE_DIR / "interview_ft.jsonl"
def build_chatml_record(question: str, answer: str, metadata: str = "", metadata_obj: dict | None = None):
    """
    CSV → ChatML messages 구조 변환 함수
    """
    system_prompt = (
        "당신은 한국어 면접 코치입니다. "
        "답변은 5~8문장으로 간결하고 논리적으로 말하세요. "
        "STAR 구조(상황-과제-행동-결과)를 자연스럽게 반영하세요."
    )

    if metadata and isinstance(metadata, str) and metadata.strip():
        system_prompt += f" 메타데이터: {metadata.strip()}"

    record = {
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": f"면접관 질문: {question.strip()}\n좋은 답변을 만들어줘."
            },
            {
                "role": "assistant",
                "content": answer.strip()
            }
        ]
    }
    # 별도 메타데이터 필드 추가(파인튜닝/후처리를 위해)
    if metadata_obj:
        record["metadata"] = metadata_obj
    return record


def main():
    print("Loading CSV:", INPUT_CSV)
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"입력 CSV를 찾을 수 없습니다: {INPUT_CSV}")
    # 모든 값을 문자열로 읽어 손실 방지
    df = pd.read_csv(INPUT_CSV, dtype=str)

    required_cols = {"question", "answer"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"CSV must contain columns: {required_cols}, but has {df.columns}")

    # 메타데이터 구성: question/answer를 제외한 모든 컬럼
    present_meta_cols = [c for c in df.columns if c not in {"question", "answer"}]

    # question/answer 공백·NULL 제거
    df["question"] = df["question"].astype(str).str.strip()
    df["answer"] = df["answer"].astype(str).str.strip()
    df = df.replace({"": pd.NA, "NaN": pd.NA, "nan": pd.NA, "NULL": pd.NA, "null": pd.NA})
    df = df.dropna(subset=["question", "answer"], how="any")

    print("Rows after dropna:", len(df))
    print("Converting to ChatML JSONL...")

    count = 0
    OUTPUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
        for _, row in df.iterrows():
            q = str(row["question"])
            a = str(row["answer"])
            # 메타데이터 문자열 및 객체 생성
            meta_obj = {}
            for c in present_meta_cols:
                val = str(row[c]).strip()
                if val and val.lower() not in {"nan", "none", "null"}:
                    meta_obj[c] = val
            # 사람이 읽기 쉬운 간단한 문자열도 system 프롬프트에 전달
            meta_str = ", ".join(f"{k}={v}" for k, v in meta_obj.items())

            rec = build_chatml_record(q, a, meta_str, meta_obj if meta_obj else None)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            count += 1

    print("Done!")
    print("Output JSONL:", OUTPUT_JSONL)
    print("Total samples written:", count)


if __name__ == "__main__":
    main()
