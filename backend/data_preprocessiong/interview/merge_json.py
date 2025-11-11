import json
from pathlib import Path
from datetime import datetime

def merge_json_files(input_dir, output_file):
    """
    디렉토리 내의 모든 JSON 파일을 하나의 JSON 파일로 병합
    """
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print(f"❌ 디렉토리를 찾을 수 없습니다: {input_path}")
        return
    
    print("=" * 70)
    print("JSON 파일 병합 스크립트")
    print("=" * 70)
    print(f"\n입력 디렉토리: {input_path}")
    print(f"출력 파일: {output_file}")
    
    # 모든 JSON 파일 찾기
    json_files = sorted(input_path.glob("*.json"))
    
    if not json_files:
        print("\n⚠ JSON 파일을 찾을 수 없습니다.")
        return
    
    print(f"\n📂 발견된 JSON 파일: {len(json_files)}개")
    
    # JSON 데이터 수집
    merged_data = []
    success_count = 0
    error_count = 0
    
    print("\n[처리 중...]")
    for idx, json_file in enumerate(json_files, 1):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                merged_data.append(data)
                success_count += 1
                
            # 진행 상황 표시 (매 100개마다)
            if idx % 100 == 0:
                print(f"  처리 중: {idx}/{len(json_files)} 파일...")
                
        except Exception as e:
            error_count += 1
            print(f"  ✗ 오류 ({json_file.name}): {e}")
    
    print(f"  처리 완료: {len(json_files)}/{len(json_files)} 파일")
    
    # 병합된 데이터를 파일로 저장
    output_path = Path(output_file)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)
        
        # 파일 크기 확인
        file_size = output_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        print("\n" + "=" * 70)
        print("✅ 병합 완료!")
        print("=" * 70)
        print(f"\n📊 통계:")
        print(f"  - 성공: {success_count}개")
        print(f"  - 실패: {error_count}개")
        print(f"  - 총 데이터: {len(merged_data)}개")
        print(f"\n📁 출력 파일:")
        print(f"  - 경로: {output_path}")
        print(f"  - 크기: {file_size_mb:.2f} MB ({file_size:,} bytes)")
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ 파일 저장 실패: {e}")

def main():
    # 기본 경로 설정
    
    # train_merged 폴더의 JSON 파일들을 병합
    train_merged_dir = Path(r"C:\dev\study\4th_mini_project\dataset\training\training_merged")
    train_output = Path(r"C:\dev\study\4th_mini_project\dataset\training\train_merged_all.json")
    
    print("\n[ TRAIN 데이터 병합 ]")
    merge_json_files(train_merged_dir, train_output)
    
    # valid_merged 폴더의 JSON 파일들을 병합
    valid_merged_dir = Path(r"C:\dev\study\4th_mini_project\dataset\valid\valid_merged")
    valid_output = Path(r"C:\dev\study\4th_mini_project\dataset\valid\valid_merged_all.json")
    
    print("\n[ VALID 데이터 병합 ]")
    merge_json_files(valid_merged_dir, valid_output)


if __name__ == "__main__":
    main()

