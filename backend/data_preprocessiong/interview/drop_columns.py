import csv
from pathlib import Path

def drop_columns(input_csv, output_csv, columns_to_drop):
    """
    CSV 파일에서 특정 컬럼들을 제거
    """
    print(f"\n처리 중: {input_csv}")
    
    # CSV 파일 읽기
    with open(input_csv, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        data = list(reader)
    
    print(f"  원본 컬럼 수: {len(headers)}개")
    print(f"  원본 데이터 수: {len(data)}개")
    
    # 존재하는 컬럼만 필터링
    existing_columns = [col for col in columns_to_drop if col in headers]
    missing_columns = [col for col in columns_to_drop if col not in headers]
    
    if missing_columns:
        print(f"  ⚠ 존재하지 않는 컬럼: {missing_columns}")
    
    # 남길 컬럼 결정
    remaining_columns = [col for col in headers if col not in existing_columns]
    
    print(f"  제거된 컬럼 수: {len(existing_columns)}개")
    print(f"  남은 컬럼 수: {len(remaining_columns)}개")
    
    # 새 CSV 파일로 저장
    with open(output_csv, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=remaining_columns)
        writer.writeheader()
        
        for row in data:
            # 제거할 컬럼을 제외한 데이터만 작성
            filtered_row = {k: v for k, v in row.items() if k in remaining_columns}
            writer.writerow(filtered_row)
    
    # 파일 크기 확인
    file_size = Path(output_csv).stat().st_size
    file_size_mb = file_size / (1024 * 1024)
    
    print(f"  ✓ 저장 완료: {output_csv}")
    print(f"  파일 크기: {file_size_mb:.2f} MB")
    
    return len(existing_columns), len(remaining_columns)

def main():
    # 제거할 컬럼 목록
    columns_to_drop = [
        # version
        'version',
        
        # info
        'date',
        'channel',
        'place',
    
        
        # question 
        'question-wordCount',
        'question-emotion',
        'question-intent',
        
        # answer
        'answer-emotion',
        'answer-emotion_text',
        'answer-intent',
        'answer-wordCount',
        'answer-intent_expression',
        'answer-intent_text',
        'answer-summary_wordCount',
        'answer-summary',
    
        # question_audio
        'question_audio-fileFormat',
        'question_audio-fileSize',
        'question_audio-duration',
        'question_audio-samplingBit',
        'question_audio-channelCount',
        'question_audio-samplingRate',
        'question_audio-audioPath',
        
        # answer_audio
        'answer_audio-fileFormat',
        'answer_audio-fileSize',
        'answer_audio-duration',
        'answer_audio-samplingBit',
        'answer_audio-channelCount',
        'answer_audio-samplingRate',
        'answer_audio-audioPath'
    ]
    
    
    print("=" * 70)
    print("CSV 컬럼 제거 스크립트")
    print("=" * 70)
    print(f"\n제거할 컬럼 수: {len(columns_to_drop)}개")
    print(f"컬럼 목록: {', '.join(columns_to_drop[:5])}...")
    
    # Train 데이터 처리
    train_input = Path(r"C:\dev\study\4th_mini_project\dataset\train_detailed_all.csv")
    train_output = Path(r"C:\dev\study\4th_mini_project\dataset\train_cleaned_all.csv")
    
    if train_input.exists():
        drop_columns(train_input, train_output, columns_to_drop)
    else:
        print(f"\n⚠ 파일을 찾을 수 없습니다: {train_input}")
    
    # Valid 데이터 처리
    valid_input = Path(r"C:\dev\study\4th_mini_project\dataset\valid_detailed_all.csv")
    valid_output = Path(r"C:\dev\study\4th_mini_project\dataset\valid_cleaned_all.csv")
    
    if valid_input.exists():
        drop_columns(valid_input, valid_output, columns_to_drop)
    else:
        print(f"\n⚠ 파일을 찾을 수 없습니다: {valid_input}")
    
    print("\n" + "=" * 70)
    print("✅ 모든 파일 처리 완료!")
    print("=" * 70)
    print(f"\n생성된 파일:")
    print(f"  - {train_output}")
    print(f"  - {valid_output}")
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()

