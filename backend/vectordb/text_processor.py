"""
텍스트 가공(3개 컬럼만 활용)
"""

from typing import List
import pandas as pd

# 임베딩할 텍스트를 구성할 컬럼 목록
COLUMNS_TO_EMBED = ("summary", "interest", "property")


def build_texts(df: pd.DataFrame) -> List[str]:
    """
    DataFrame을 받아 RAG 검색용 'text' 본문 문자열 리스트를 생성합니다.
    (summary, interest, property 3개 컬럼 활용)
    """
    print(f"RAG 본문(text) 생성을 위해 {list(COLUMNS_TO_EMBED)} 컬럼을 사용합니다.")

    selected = df[list(COLUMNS_TO_EMBED)].fillna("")
    texts = []

    for row in selected.itertuples(index=False, name=None):
        pieces = []
        for col_name, value in zip(selected.columns, row, strict=False):
            value_str = str(value).strip()
            if not value_str:
                continue

            if col_name == "summary":
                label = "학과 요약"
            elif col_name == "interest":
                label = "관련 관심사"
            elif col_name == "property":
                label = "학과 특징"
            else:
                label = col_name.capitalize()

            pieces.append(f"{label}: {value_str}")

        texts.append("\n\n".join(pieces))
    return texts


def chunk_dataframe(df: pd.DataFrame, paragraphs_per_chunk: int = 2) -> pd.DataFrame:
    """
    한 학과 텍스트를 여러 개의 짧은 문단(기본 2개 단위) 청크로 나눕니다.
    """
    if "text" not in df.columns:
        raise ValueError("chunk_dataframe을 사용하려면 'text' 컬럼이 필요합니다.")

    chunked_rows = []
    for _, row in df.iterrows():
        paragraphs = [p.strip() for p in str(row["text"]).split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [""]

        for start in range(0, len(paragraphs), paragraphs_per_chunk):
            chunk_paragraphs = paragraphs[start : start + paragraphs_per_chunk]
            chunk_text = "\n\n".join(chunk_paragraphs)

            new_row = row.copy()
            new_row["text"] = chunk_text
            new_row["chunkIndex"] = start // paragraphs_per_chunk
            chunked_rows.append(new_row)

    chunked_df = pd.DataFrame(chunked_rows)
    chunked_df.reset_index(drop=True, inplace=True)
    return chunked_df
