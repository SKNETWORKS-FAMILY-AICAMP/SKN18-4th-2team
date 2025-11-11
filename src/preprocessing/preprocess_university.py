import re
import json
import pandas as pd
from pathlib import Path

# =====================================================
# 📁 경로 설정
# =====================================================
BASE_DIR = Path(__file__).resolve().parents[2] / "data"
RAW_DIR = BASE_DIR / "raw" / "university"
PROCESSED_DIR = BASE_DIR / "processed" / "university"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# =====================================================
# 🧹 텍스트 정제
# =====================================================
def clean_text(text: str) -> str:
    if pd.isna(text):
        return ""
    text = str(text)
    text = re.sub(r"<[^>]+>", "", text)                # HTML 태그 제거
    text = re.sub(r"[^\w\s.,!?%()·~\-]", "", text)     # 특수문자 제거
    text = re.sub(r"\s+", " ", text).strip()           # 공백 정리
    return text

# =====================================================
# 📦 전처리 함수
# =====================================================
def preprocess(file_path: Path):
    df = pd.read_csv(file_path, encoding="utf-8-sig")

    # 한글 컬럼명 → 표준 이름 매핑
    rename_map = {
        "요약": "summary",
        "관심분야": "interest",
        "특성": "property",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # 필수 컬럼 확인
    required_cols = ["summary", "interest", "property"]
    if not set(required_cols).issubset(df.columns):
        print(f"⚠️ {file_path.name} → 필수 컬럼 누락 ({required_cols})")
        return

    # 텍스트 정제 (필수 칼럼만)
    for col in required_cols:
        df[col] = df[col].apply(clean_text)

    # 나머지 컬럼 → metadata JSON
    metadata_cols = [c for c in df.columns if c not in required_cols]
    df["metadata"] = df[metadata_cols].to_dict(orient="records")
    df["metadata"] = df["metadata"].apply(lambda x: json.dumps(x, ensure_ascii=False))

    # 불필요한 원본 칼럼 제거
    df = df[required_cols + ["metadata"]]

    # 저장
    out_path = PROCESSED_DIR / file_path.name
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"✅ {file_path.name} → {out_path.name} 저장 완료 ({len(df)}행)")

# =====================================================
# 🚀 메인
# =====================================================
def main():
    files = list(RAW_DIR.glob("major_details_*.csv"))
    if not files:
        print("⚠️ raw/university 폴더에 major_details_*.csv 파일이 없습니다.")
        return
    for f in files:
        preprocess(f)

if __name__ == "__main__":
    main()
