import csv
from pathlib import Path

def filter_experienced_and_add_sample_id(input_csv, output_csv):
    """
    1. EXPERIENCED 행만 추출
    2. sample_id 부여
    3. 컬럼별 결측치 조회
    """
    print("=" * 70)
    print("EXPERIENCED 데이터 필터링 및 Sample ID 부여")
    print("=" * 70)
    print(f"\n입력 파일: {input_csv}")
    print(f"출력 파일: {output_csv}")
    
    try:
        # CSV 파일 읽기
        print("\n[1단계] CSV 파일 로딩 중...")
        with open(input_csv, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            all_rows = list(reader)
        
        print(f"  ✓ 총 {len(all_rows)}개 행 로드 완료")
        print(f"  ✓ 컬럼 수: {len(headers)}개")
        
        # EXPERIENCED 행만 필터링
        print("\n[2단계] EXPERIENCED 데이터 필터링 중...")
        experienced_rows = [row for row in all_rows if row.get('experience', '').upper() == 'EXPERIENCED']
        
        print(f"  ✓ EXPERIENCED 행: {len(experienced_rows)}개")
        print(f"  ✓ 필터링 전: {len(all_rows)}개 → 필터링 후: {len(experienced_rows)}개")
        
        if len(experienced_rows) == 0:
            print("\n⚠ EXPERIENCED 데이터가 없습니다.")
            return
        
        # sample_id 추가 (첫 번째 컬럼으로)
        print("\n[3단계] Sample ID 부여 중...")
        new_headers = ['sample_id'] + list(headers)
        
        for idx, row in enumerate(experienced_rows, 1):
            row['sample_id'] = idx
        
        print(f"  ✓ Sample ID 범위: 1 ~ {len(experienced_rows)}")
        
        # CSV 파일 저장
        print("\n[4단계] 파일 저장 중...")
        with open(output_csv, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=new_headers)
            writer.writeheader()
            writer.writerows(experienced_rows)
        
        print(f"  ✓ 저장 완료: {output_csv}")
        
        # 컬럼별 결측치 조회
        print("\n[5단계] 컬럼별 결측치 조회 중...")
        
        # 저장된 파일을 다시 읽어서 결측치 확인
        with open(output_csv, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            data_rows = list(reader)
        
        print("\n" + "=" * 70)
        print("📊 컬럼별 결측치 통계")
        print("=" * 70)
        
        missing_stats = []
        total_rows = len(data_rows)
        
        for col in new_headers:
            missing_count = sum(1 for row in data_rows if not row.get(col) or row.get(col).strip() == '')
            missing_percent = (missing_count / total_rows) * 100 if total_rows > 0 else 0
            missing_stats.append({
                '컬럼명': col,
                '결측치 수': missing_count,
                '결측치 비율(%)': f"{missing_percent:.2f}%",
                '유효 데이터 수': total_rows - missing_count
            })
        
        # 결측치가 있는 컬럼만 표시
        missing_cols = [stat for stat in missing_stats if stat['결측치 수'] > 0]
        
        if missing_cols:
            print(f"\n⚠ 결측치가 있는 컬럼: {len(missing_cols)}개")
            print("\n" + "-" * 70)
            print(f"{'컬럼명':<35} {'결측치 수':<12} {'결측치 비율':<15} {'유효 데이터 수':<15}")
            print("-" * 70)
            for stat in missing_cols:
                print(f"{stat['컬럼명']:<35} {stat['결측치 수']:<12} {stat['결측치 비율(%)']:<15} {stat['유효 데이터 수']:<15}")
        else:
            print("\n✅ 결측치가 있는 컬럼이 없습니다!")
        
        # 전체 통계 요약
        print("\n" + "-" * 70)
        print(f"{'전체 통계':<30} {'값':<12}")
        print("-" * 70)
        print(f"{'총 행 수':<30} {total_rows:<12}")
        print(f"{'총 컬럼 수':<30} {len(new_headers):<12}")
        print(f"{'결측치가 있는 컬럼 수':<30} {len(missing_cols):<12}")
        total_missing = sum(stat['결측치 수'] for stat in missing_stats)
        print(f"{'전체 결측치 수':<30} {total_missing:<12}")
        
        # 파일 크기 확인
        file_size = Path(output_csv).stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        print("\n" + "=" * 70)
        print("✅ 처리 완료!")
        print("=" * 70)
        print(f"\n📁 출력 파일:")
        print(f"  - 경로: {output_csv}")
        print(f"  - 크기: {file_size_mb:.2f} MB ({file_size:,} bytes)")
        print(f"  - 행 수: {len(experienced_rows)}개")
        print(f"  - 컬럼 수: {len(new_headers)}개")
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

def main():
    # Train 데이터 처리
    train_input = Path(r"C:\dev\study\4th_mini_project\dataset\merged_all.csv")
    train_output = Path(r"C:\dev\study\4th_mini_project\dataset\merged_experienced.csv")
    
    if train_input.exists():
        filter_experienced_and_add_sample_id(train_input, train_output)
    else:
        print(f"❌ 파일을 찾을 수 없습니다: {train_input}")
    
    # # Valid 데이터 처리
    # print("\n\n")
    # valid_input = Path(r"C:\dev\study\4th_mini_project\dataset\valid_cleaned_all.csv")
    # valid_output = Path(r"C:\dev\study\4th_mini_project\dataset\valid_experienced.csv")
    
    # if valid_input.exists():
    #     filter_experienced_and_add_sample_id(valid_input, valid_output)
    # else:
    #     print(f"❌ 파일을 찾을 수 없습니다: {valid_input}")

if __name__ == "__main__":
    main()

