import csv
from pathlib import Path

def add_sample_id(input_csv, output_csv):
    """
    CSV 파일에 sample_id 컬럼을 추가합니다.
    """
    print("=" * 70)
    print("Sample ID 추가 스크립트")
    print("=" * 70)
    print(f"\n입력 파일: {input_csv}")
    print(f"출력 파일: {output_csv}")
    
    try:
        # CSV 파일 읽기
        with open(input_csv, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            fieldnames = reader.fieldnames
        
        print(f"\n[1단계] 데이터 로드 완료")
        print(f"  - 총 행 수: {len(rows)}개")
        print(f"  - 기존 컬럼 수: {len(fieldnames)}개")
        
        # sample_id를 첫 번째 컬럼으로 추가
        new_fieldnames = ['sample_id'] + list(fieldnames)
        
        # 각 행에 sample_id 추가 (1부터 시작)
        for idx, row in enumerate(rows, 1):
            row['sample_id'] = idx
        
        print(f"\n[2단계] Sample ID 추가 완료")
        print(f"  - 새로운 컬럼 수: {len(new_fieldnames)}개")
        
        # CSV 파일 쓰기
        with open(output_csv, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=new_fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        print(f"\n[3단계] 파일 저장 완료")
        
        # 파일 크기 확인
        file_size = Path(output_csv).stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        print("\n" + "=" * 70)
        print("✅ 완료!")
        print("=" * 70)
        print(f"\n📊 통계:")
        print(f"  - 총 행 수: {len(rows)}개")
        print(f"  - 컬럼 수: {len(new_fieldnames)}개")
        print(f"  - Sample ID 범위: 1 ~ {len(rows)}")
        print(f"\n📁 출력 파일:")
        print(f"  - 경로: {output_csv}")
        print(f"  - 크기: {file_size_mb:.2f} MB ({file_size:,} bytes)")
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")

def main():
    # Valid 파일 처리
    valid_input = Path(r"C:\dev\study\4th_mini_project\dataset\ICT\valid_cleaned.csv")
    valid_output = Path(r"C:\dev\study\4th_mini_project\dataset\ICT\valid_cleaned.csv")
    
    if valid_input.exists():
        add_sample_id(valid_input, valid_output)
    else:
        print(f"❌ 파일을 찾을 수 없습니다: {valid_input}")
    
    # Train 파일도 처리
    print("\n\n")
    train_input = Path(r"C:\dev\study\4th_mini_project\dataset\ICT\train_cleaned.csv")
    train_output = Path(r"C:\dev\study\4th_mini_project\dataset\ICT\train_cleaned.csv")
    
    if train_input.exists():
        add_sample_id(train_input, train_output)
    else:
        print(f"❌ 파일을 찾을 수 없습니다: {train_input}")

if __name__ == "__main__":
    main()

