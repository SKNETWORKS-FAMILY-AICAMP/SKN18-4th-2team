# vectordb/data_loader.py
import pandas as pd
from pathlib import Path
from typing import List, Iterable

def read_csv(path: Path, *, columns: Iterable[str]) -> pd.DataFrame:
    """단일 CSV 파일을 다중 인코딩으로 읽습니다."""
    encodings = ("utf-8", "utf-8-sig", "cp949", "euc-kr")
    last_error: Exception | None = None
    
    for encoding in encodings:
        try:
            df = pd.read_csv(path, encoding=encoding)
            # 필수 컬럼 확인
            missing = [col for col in columns if col not in df.columns]
            if missing:
                raise ValueError(f"{path.name} 파일에 필수 컬럼이 없습니다: {missing}")
            return df
        except UnicodeDecodeError as exc:
            last_error = exc
    else:
        raise RuntimeError(f"{path} 파일 디코딩에 실패: {path}") from last_error

def load_major_data(data_dir: str, required_columns: List[str]) -> pd.DataFrame:
    """
    data_dir에서 'major_details_*.csv' 파일들을 찾아
    하나의 DataFrame으로 통합합니다.
    """
    data_path = Path(data_dir)
    csv_files = sorted(data_path.glob("major_details_*.csv"))
    
    if not csv_files:
        raise SystemExit(f"{data_dir} 디렉터리에서 'major_details_*.csv' 파일을 찾을 수 없습니다.")
        
    print(f"총 {len(csv_files)}개의 CSV 파일 로드 중...")
    all_dfs = []
    for csv_path in csv_files:
        print(f" - {csv_path.name} 읽는 중...")
        try:
            df = read_csv(csv_path, columns=required_columns)
            all_dfs.append(df)
        except Exception as e:
            print(f"   [경고] {csv_path.name} 파일 처리 중 오류 발생: {e}")
            
    df_combined = pd.concat(all_dfs, ignore_index=True)
    
    # 중복 제거 (majorSeq 기준)
    df_combined.drop_duplicates(subset=["majorSeq"], keep='first', inplace=True)
    
    print(f"데이터 통합 완료. (총 {len(df_combined)}개 학과)")
    return df_combined