"""
RAG에 사용할 단일 임베딩 JSONL 파일을 생성하는 유틸리티 스크립트입니다.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, List

import pandas as pd
from sentence_transformers import SentenceTransformer
import time

def parse_args() -> argparse.Namespace:
    """스크립트 실행 인자를 파싱합니다."""
    parser = argparse.ArgumentParser(description="학과 데이터 CSV 파일에 대한 임베딩을 생성합니다.")
    parser.add_argument(
        "--data-dir",
        default="backend/data",
        help="입력 CSV 파일들(major_details_*.csv)이 포함된 디렉터리.",
    )
    parser.add_argument(
        "--output-file",
        default="majors_embeddings.jsonl",
        help="임베딩 결과가 저장될 최종 JSONL 파일 경로.",
    )
    parser.add_argument(
        "--model",
        default="jhgan/ko-sroberta-multitask",
        help="사용할 SentenceTransformer 모델 이름. (한국어 권장)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="임베딩 처리 배치 크기.",
    )
    parser.add_argument(
        "--normalize",
        action="store_true",
        help="임베딩에 L2 정규화를 적용합니다. (코사인 유사도 사용 시 권장)",
    )
    return parser.parse_args()


def read_csv(path: Path, *, columns: Iterable[str]) -> pd.DataFrame:
    """
    다양한 인코딩(utf-8, cp949 등)을 시도하여 CSV 파일을 읽습니다.
    필수 컬럼 존재 여부도 확인합니다.
    """
    encodings = ("utf-8", "utf-8-sig", "cp949", "euc-kr")
    last_error: Exception | None = None
    
    for encoding in encodings:
        try:
            df = pd.read_csv(path, encoding=encoding)
            break
        except UnicodeDecodeError as exc:
            last_error = exc
    else:
        raise RuntimeError(f"{path} 파일 디코딩에 실패했습니다. (지원 인코딩: {encodings})") from last_error

    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(f"{path.name} 파일에 필수 컬럼이 없습니다: {missing}")
    return df


def build_texts(df: pd.DataFrame, columns: Iterable[str]) -> List[str]:
    """
    RAG 검색의 '문맥(Context)'이 될 단일 텍스트 문자열을 생성합니다.
    (예: "학과 요약: ... \n\n 관련 흥미: ... \n\n 학과 특징: ...")
    """
    selected = df[list(columns)].fillna("") # NaN 값을 빈 문자열로
    texts = []
    
    for row in selected.itertuples(index=False, name=None):
        pieces = []
        # ('summary', 'interest', 'property') 순서로
        for col_name, value in zip(selected.columns, row, strict=False):
            value_str = str(value).strip()
            if not value_str:
                continue
            
            # 라벨을 붙여서 텍스트 품질 향상
            if col_name == 'summary':
                label = "학과 요약"
            elif col_name == 'interest':
                label = "관련 흥미"
            elif col_name == 'property':
                label = "학과 특징"
            else:
                label = col_name.capitalize()
                
            pieces.append(f"{label}: {value_str}")
            
        # 각 항목을 두 줄 띄어쓰기(\n\n)로 구분
        texts.append("\n\n".join(pieces))
    return texts


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    """데이터(dict) 목록을 JSONL (JSON Lines) 파일로 저장합니다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False))
            fh.write("\n")

def main() -> None:
    """메인 실행 함수"""
    args = parse_args()
    data_dir = Path(args.data_dir)
    output_file = Path(args.output_file)
    
    # 임베딩할 텍스트를 구성할 핵심 컬럼 3가지
    columns = ("summary", "interest", "property") # <-- 이 변수를 재활용합니다

    # 1. 데이터 로드: 'major_details_'로 시작하는 모든 CSV를 찾음
    csv_files = sorted(data_dir.glob("major_details_*.csv"))
    if not csv_files:
        raise SystemExit(f"{data_dir} 디렉터리에서 'major_details_*.csv' 파일을 찾을 수 없습니다.")
    
    print(f"총 {len(csv_files)}개의 CSV 파일 로드 중...")
    
    all_dfs = []
    for csv_path in csv_files:
        print(f" - {csv_path.name} 읽는 중...")
        try:
            df = read_csv(csv_path, columns=columns)
            all_dfs.append(df)
        except Exception as e:
            print(f"   [경고] {csv_path.name} 파일 처리 중 오류 발생: {e}")
            
    # 2. 데이터 통합
    df_combined = pd.concat(all_dfs, ignore_index=True)
    print(f"데이터 통합 완료. (총 {len(df_combined)}개 학과)")

    # 3. 임베딩 모델 로드
    print(f"임베딩 모델 로드 중: {args.model}")
    start_time = time.time()
    model = SentenceTransformer(args.model)
    print(f"모델 로드 완료. ({time.time() - start_time:.2f}초)")

    # 4. 임베딩할 텍스트 생성
    texts = build_texts(df_combined, columns=columns)

    # 5. 임베딩 실행
    print(f"{len(texts)}개 텍스트 임베딩 시작 (배치 크기: {args.batch_size})...")
    start_time = time.time()
    embeddings = model.encode(
        texts,
        batch_size=args.batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=args.normalize,
    )
    print(f"임베딩 완료. ({time.time() - start_time:.2f}초)")
    
    # 6. JSONL 파일로 저장할 레코드(dict) 생성
    print("JSONL 레코드 생성 중...")
    records = []
    
    # 임베딩에 사용된 컬럼 목록 (삭제 대상)
    columns_to_remove = set(columns) # {"summary", "interest", "property"}

    # df_combined.itertuples()는 각 행(row)을 'named tuple'로 반환합니다.
    for row, text, embedding in zip(df_combined.itertuples(index=False), texts, embeddings, strict=False):
        
        # 1. 'row'를 딕셔너리로 변환 (모든 원본 컬럼이 포함됨)
        record = row._asdict()
        
        # 2. RAG 필수 필드 추가
        record['text'] = text                 # 임베딩된 '본문'
        record['embedding'] = embedding.tolist() # '벡터'
        
        # 3. 메타데이터 정리: 임베딩에 사용된 원본 컬럼 3개 삭제
        #    (이제 'text' 필드에 합쳐졌으므로 중복/불필요)
        for col in columns_to_remove:
            if col in record:
                del record[col]
        
        # (만약 'text_for_embedding' 컬럼이 원본 df에 남아있었다면 삭제)
        if 'text_for_embedding' in record:
            del record['text_for_embedding']
        
        records.append(record)

    # 7. JSONL 파일로 저장
    write_jsonl(output_file, records)
    print(f"\n--- 작업 완료! ---")
    print(f"총 {len(records)}개의 레코드를 {output_file} 파일로 저장했습니다.")


if __name__ == "__main__":
    main()