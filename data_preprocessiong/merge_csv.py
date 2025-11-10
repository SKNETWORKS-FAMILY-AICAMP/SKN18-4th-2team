import csv
from pathlib import Path

def merge_csv_files(train_csv, valid_csv, output_csv):
    """
    Train과 Valid CSV 파일을 하나로 병합
    """
    print("=" * 70)
    print("CSV 파일 병합 스크립트")
    print("=" * 70)
    print(f"\n입력 파일:")
    print(f"  - Train: {train_csv}")
    print(f"  - Valid: {valid_csv}")
    print(f"\n출력 파일: {output_csv}")
    
    try:
        # Train 파일 읽기
        print("\n[1단계] Train 파일 로딩 중...")
        with open(train_csv, 'r', encoding='utf-8-sig', newline='') as f:
            train_reader = csv.DictReader(f)
            train_headers = train_reader.fieldnames
            train_rows = list(train_reader)
        
        print(f"  ✓ Train 행 수: {len(train_rows)}개")
        print(f"  ✓ Train 컬럼 수: {len(train_headers)}개")
        
        # Valid 파일 읽기
        print("\n[2단계] Valid 파일 로딩 중...")
        with open(valid_csv, 'r', encoding='utf-8-sig', newline='') as f:
            valid_reader = csv.DictReader(f)
            valid_headers = valid_reader.fieldnames
            valid_rows = list(valid_reader)
        
        print(f"  ✓ Valid 행 수: {len(valid_rows)}개")
        print(f"  ✓ Valid 컬럼 수: {len(valid_headers)}개")
        
        # 헤더 확인 및 통합
        print("\n[3단계] 헤더 확인 중...")
        if set(train_headers) != set(valid_headers):
            print("  ⚠ 경고: Train과 Valid의 컬럼이 일치하지 않습니다!")
            print(f"  Train 컬럼: {train_headers}")
            print(f"  Valid 컬럼: {valid_headers}")
            
            # 공통 컬럼만 사용
            common_headers = sorted(set(train_headers) & set(valid_headers))
            print(f"\n  → 공통 컬럼 사용: {len(common_headers)}개")
            headers = common_headers
        else:
            headers = train_headers
            print(f"  ✓ 컬럼 일치 확인: {len(headers)}개")
        
        # 데이터 병합
        print("\n[4단계] 데이터 병합 중...")
        merged_rows = train_rows + valid_rows
        
        print(f"  ✓ 병합된 행 수: {len(merged_rows)}개")
        print(f"    - Train: {len(train_rows)}개")
        print(f"    - Valid: {len(valid_rows)}개")
        
        # CSV 파일 저장
        print("\n[5단계] 파일 저장 중...")
        with open(output_csv, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            
            # Train 데이터 작성
            for row in train_rows:
                filtered_row = {k: v for k, v in row.items() if k in headers}
                writer.writerow(filtered_row)
            
            # Valid 데이터 작성
            for row in valid_rows:
                filtered_row = {k: v for k, v in row.items() if k in headers}
                writer.writerow(filtered_row)
        
        print(f"  ✓ 저장 완료: {output_csv}")
        
        # 파일 크기 확인
        file_size = Path(output_csv).stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        print("\n" + "=" * 70)
        print("✅ 병합 완료!")
        print("=" * 70)
        print(f"\n📊 통계:")
        print(f"  - Train 행 수: {len(train_rows)}개")
        print(f"  - Valid 행 수: {len(valid_rows)}개")
        print(f"  - 총 행 수: {len(merged_rows)}개")
        print(f"  - 컬럼 수: {len(headers)}개")
        print(f"\n📁 출력 파일:")
        print(f"  - 경로: {output_csv}")
        print(f"  - 크기: {file_size_mb:.2f} MB ({file_size:,} bytes)")
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

def main():
    train_csv = Path(r"C:\dev\study\4th_mini_project\dataset\train_cleaned_all.csv")
    valid_csv = Path(r"C:\dev\study\4th_mini_project\dataset\valid_cleaned_all.csv")
    output_csv = Path(r"C:\dev\study\4th_mini_project\dataset\merged_all.csv")
    
    if not train_csv.exists():
        print(f"❌ Train 파일을 찾을 수 없습니다: {train_csv}")
        return
    
    if not valid_csv.exists():
        print(f"❌ Valid 파일을 찾을 수 없습니다: {valid_csv}")
        return
    
    merge_csv_files(train_csv, valid_csv, output_csv)

if __name__ == "__main__":
    main()

