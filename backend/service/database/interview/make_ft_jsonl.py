import os
import json
import pandas as pd


# 상대 경로 (현재 파일 기준)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.join(BASE_DIR, "valid_merged_all_preprocessed.csv")
OUTPUT_JSONL = os.path.join(BASE_DIR, "interview_sft_chatml.jsonl")


def build_chatml_record(question: str, answer: str, metadata: str = ""):
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
    return record


def main():
    print("✅ Loading CSV:", INPUT_CSV)
    df = pd.read_csv(INPUT_CSV)

    required_cols = {"question", "answer"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"CSV must contain columns: {required_cols}, but has {df.columns}")

    # optional metadata column
    use_metadata = "metadata" in df.columns

    print("✅ Rows:", len(df))
    print("✅ Converting to ChatML JSONL...")

    count = 0
    with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
        for _, row in df.iterrows():
            q = str(row["question"])
            a = str(row["answer"])
            meta = str(row["metadata"]) if use_metadata else ""

            rec = build_chatml_record(q, a, meta)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            count += 1

    print("🎉 Done!")
    print("✅ Output JSONL:", OUTPUT_JSONL)
    print("✅ Total samples written:", count)


if __name__ == "__main__":
    main()
