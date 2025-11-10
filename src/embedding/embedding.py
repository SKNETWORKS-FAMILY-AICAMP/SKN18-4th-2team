import os
import pandas as pd
import numpy as np
import torch
from pathlib import Path
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

# -----------------------------
# 경로 설정
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
PREPROCESS_DIR = BASE_DIR / "preprocessing"
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------
# 임베딩 모델 로드
# -----------------------------
print("🧠 임베딩 모델 로드 중...")
model_name = "intfloat/multilingual-e5-large"  # or "BM-K/KoSimCSE-roberta-large"
model = SentenceTransformer(model_name)
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)
print(f"✅ 모델 로드 완료 (device = {device})")

# -----------------------------
# CSV 불러오기
# -----------------------------
train_path = PREPROCESS_DIR / "processed_train.csv"
valid_path = PREPROCESS_DIR / "processed_valid.csv"

train_df = pd.read_csv(train_path)
valid_df = pd.read_csv(valid_path)
print(f"📄 Train: {len(train_df)} rows | Valid: {len(valid_df)} rows")

# -----------------------------
# 임베딩 생성 함수
# -----------------------------
def create_embeddings(texts, batch_size=32):
    """SentenceTransformer 기반 배치 임베딩"""
    embeddings = []
    for i in tqdm(range(0, len(texts), batch_size), desc="🔹 Embedding batches"):
        batch_texts = texts[i:i+batch_size]
        batch_embeddings = model.encode(batch_texts, show_progress_bar=False, convert_to_numpy=True)
        embeddings.append(batch_embeddings)
    return np.vstack(embeddings)

# -----------------------------
# Summary 컬럼 기반 임베딩 생성
# -----------------------------
print("🚀 Summary 컬럼 임베딩 생성 중...")
train_embeddings = create_embeddings(train_df["summary"].fillna("").tolist())
valid_embeddings = create_embeddings(valid_df["summary"].fillna("").tolist())
print("✅ 임베딩 생성 완료!")

# -----------------------------
# 저장 (.npy / .csv)
# -----------------------------
np.save(OUTPUT_DIR / "train_summary_embeddings.npy", train_embeddings)
np.save(OUTPUT_DIR / "valid_summary_embeddings.npy", valid_embeddings)

train_embed_df = pd.DataFrame(train_embeddings)
valid_embed_df = pd.DataFrame(valid_embeddings)
train_embed_df.to_csv(OUTPUT_DIR / "train_summary_embeddings.csv", index=False)
valid_embed_df.to_csv(OUTPUT_DIR / "valid_summary_embeddings.csv", index=False)

print("💾 임베딩 저장 완료!")
print(f"📁 저장 경로: {OUTPUT_DIR}")
