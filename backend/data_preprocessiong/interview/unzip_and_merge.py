import os
import zipfile
import shutil
from pathlib import Path

def extract_zip_files(directory, extract_to):
    """
    디렉토리 내의 모든 zip 파일 압축 해제
    """
    print(f"\n[압축 해제] {directory.name} 디렉토리 처리 중...")
    zip_files = list(Path(directory).glob("*.zip"))
    
    if not zip_files:
        print(f"  ⚠ zip 파일이 없습니다.")
        return 0
    
    for zip_file in zip_files:
        # 각 zip 파일을 개별 폴더에 압축 해제
        extract_folder = extract_to / zip_file.stem
        
        try:
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(extract_folder)
            print(f"  ✓ {zip_file.name} 압축 해제 완료")
        except Exception as e:
            print(f"  ✗ {zip_file.name} 압축 해제 실패: {e}")
    
    return len(zip_files)

def merge_extracted_data(extracted_dir, output_dir):
    """
    압축 해제된 데이터를 하나의 디렉토리로 병합
    """
    print(f"\n[병합] {extracted_dir.name} → {output_dir.name}")
    
    if not extracted_dir.exists():
        print(f"  ⚠ {extracted_dir} 디렉토리가 존재하지 않습니다.")
        return 0
    
    # 출력 디렉토리 생성
    output_dir.mkdir(parents=True, exist_ok=True)
    
    copied_count = 0
    file_count = 0
    
    # 압축 해제된 각 폴더의 내용을 병합
    for item in extracted_dir.iterdir():
        if item.is_dir():
            print(f"  - {item.name} 처리 중...")
            # 각 폴더 내의 파일들을 output_dir로 복사
            for file_item in item.rglob('*'):
                if file_item.is_file():
                    # 상대 경로 유지하면서 복사
                    relative_path = file_item.relative_to(item)
                    dest_file = output_dir / relative_path
                    
                    # 대상 디렉토리 생성
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 파일 복사
                    if not dest_file.exists():
                        shutil.copy2(file_item, dest_file)
                        file_count += 1
            
            copied_count += 1
            print(f"    ✓ 완료")
    
    return copied_count, file_count

def main():
    # 기본 경로 설정 - ICT 폴더
    # base_dir = Path(r"C:\dev\study\4th_mini_project\dataset\ICT")
    # train_dir = base_dir / "train"
    valid_dir = Path(r"C:\dev\study\4th_mini_project\dataset\training")
    
    # 압축 해제 경로
    # train_extracted = base_dir / "train_extracted"
    valid_extracted = valid_dir / "training_extracted"
    
    # 병합된 데이터 경로 (train끼리, valid끼리 각각)
    #train_merged = base_dir / "train_merged"
    valid_merged = valid_dir / "training_merged"
    
    # print("=" * 70)
    # print("ICT 데이터셋 압축 해제 및 병합 스크립트")
    # print("=" * 70)
    # print(f"\n작업 디렉토리: {base_dir}")
    
    # # 1. train 디렉토리 처리
    # print("\n" + "=" * 70)
    # print("[ TRAIN 데이터 처리 ]")
    # print("=" * 70)
    
    # if train_dir.exists():
    #     # 압축 해제
    #     extracted_count = extract_zip_files(train_dir, train_extracted)
    #     print(f"\n  → {extracted_count}개의 zip 파일 압축 해제 완료")
        
    #     # 병합
    #     if extracted_count > 0:
    #         folder_count, file_count = merge_extracted_data(train_extracted, train_merged)
    #         print(f"\n  → {folder_count}개 폴더, {file_count}개 파일 병합 완료")
    # else:
    #     print(f"\n⚠ train 디렉토리를 찾을 수 없습니다: {train_dir}")
    
    # 2. valid 디렉토리 처리
    print("\n" + "=" * 70)
    print("[ VALID 데이터 처리 ]")
    print("=" * 70)
    
    if valid_dir.exists():
        # 압축 해제
        extracted_count = extract_zip_files(valid_dir, valid_extracted)
        print(f"\n  → {extracted_count}개의 zip 파일 압축 해제 완료")
        
        # 병합
        if extracted_count > 0:
            folder_count, file_count = merge_extracted_data(valid_extracted, valid_merged)
            print(f"\n  → {folder_count}개 폴더, {file_count}개 파일 병합 완료")
    else:
        print(f"\n⚠ valid 디렉토리를 찾을 수 없습니다: {valid_dir}")
    
    # 최종 결과 출력
    print("\n" + "=" * 70)
    print("작업 완료!")
    print("=" * 70)
    print(f"\n📁 결과 디렉토리:")
    # print(f"  ✓ Train 병합 데이터: {train_merged}")
    print(f"  ✓ Valid 병합 데이터: {valid_merged}")
    print(f"\n📂 중간 파일 (압축 해제):")
    # print(f"  - {train_extracted}")
    print(f"  - {valid_extracted}")
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()

