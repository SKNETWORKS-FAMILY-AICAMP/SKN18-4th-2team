import json
import csv
from pathlib import Path

def flatten_json_to_csv(json_file, csv_file):
    """
    JSON 파일을 완전히 평면화하여 CSV로 변환
    """
    print("=" * 70)
    print("JSON to CSV 상세 변환 스크립트")
    print("=" * 70)
    print(f"\n입력 파일: {json_file}")
    print(f"출력 파일: {csv_file}")
    
    # JSON 파일 읽기
    print("\n[1단계] JSON 파일 로딩 중...")
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"  ✓ {len(data)}개의 데이터 로드 완료")
    except Exception as e:
        print(f"  ✗ JSON 파일 로드 실패: {e}")
        return
    
    # CSV 헤더 정의 (상위-하위 형식)
    print("\n[2단계] CSV 변환 중...")
    
    headers = [
        # version
        'version',
        
        # info
        'date',
        'occupation',
        'channel',
        'place',
        'gender',
        'ageRange',
        'experience',
        
        # question
        'question',
        'question-wordCount',
        'question-emotion',
        'question-intent',
        
        # answer
        'answer',
        'answer-wordCount',
        'answer-emotion',
        'answer-emotion_text',
        'answer-emotion_expression',
        'answer-emotion_category',
        'answer-intent',
        'answer-intent_text',
        'answer-intent_expression',
        'answer-intent_category',
        'answer-summary',
        'answer-summary_wordCount',
        
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
    
    try:
        with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            
            success_count = 0
            error_count = 0
            
            for idx, item in enumerate(data, 1):
                try:
                    # 데이터 추출
                    version = item.get('version', '')
                    dataset = item.get('dataSet', {})
                    info = dataset.get('info', {})
                    question = dataset.get('question', {})
                    answer = dataset.get('answer', {})
                    raw_data_info = item.get('rawDataInfo', {})
                    
                    # emotion과 intent를 JSON 문자열로 변환
                    question_emotion = json.dumps(question.get('emotion', []), ensure_ascii=False)
                    question_intent = json.dumps(question.get('intent', []), ensure_ascii=False)
                    answer_emotion_list = answer.get('emotion', [])
                    answer_emotion = json.dumps(answer_emotion_list, ensure_ascii=False)
                    answer_intent_list = answer.get('intent', [])
                    answer_intent = json.dumps(answer_intent_list, ensure_ascii=False)
                    
                    # answer emotion의 첫 번째 항목 정보 추출
                    answer_emotion_0_text = ''
                    answer_emotion_0_expression = ''
                    answer_emotion_0_category = ''
                    if answer_emotion_list and len(answer_emotion_list) > 0:
                        first_emotion = answer_emotion_list[0]
                        answer_emotion_0_text = first_emotion.get('text', '')
                        answer_emotion_0_expression = first_emotion.get('expression', '')
                        answer_emotion_0_category = first_emotion.get('category', '')
                    
                    # answer intent의 첫 번째 항목 정보 추출
                    answer_intent_0_text = ''
                    answer_intent_0_expression = ''
                    answer_intent_0_category = ''
                    if answer_intent_list and len(answer_intent_list) > 0:
                        first_intent = answer_intent_list[0]
                        answer_intent_0_text = first_intent.get('text', '')
                        answer_intent_0_expression = first_intent.get('expression', '')
                        answer_intent_0_category = first_intent.get('category', '')
                    
                    # CSV 행 생성
                    row = {
                        'version': version,
                        
                        # info
                        'date': info.get('date', ''),
                        'occupation': info.get('occupation', ''),
                        'channel': info.get('channel', ''),
                        'place': info.get('place', ''),
                        'gender': info.get('gender', ''),
                        'ageRange': info.get('ageRange', ''),
                        'experience': info.get('experience', ''),
                        
                        # question
                        'question': question.get('raw', {}).get('text', ''),
                        'question-wordCount': question.get('raw', {}).get('wordCount', ''),
                        'question-emotion': question_emotion,
                        'question-intent': question_intent,
                        
                        # answer
                        'answer': answer.get('raw', {}).get('text', ''),
                        'answer-wordCount': answer.get('raw', {}).get('wordCount', ''),
                        'answer-emotion': answer_emotion,
                        'answer-emotion_text': answer_emotion_0_text,
                        'answer-emotion_expression': answer_emotion_0_expression,
                        'answer-emotion_category': answer_emotion_0_category,
                        'answer-intent': answer_intent,
                        'answer-intent_text': answer_intent_0_text,
                        'answer-intent_expression': answer_intent_0_expression,
                        'answer-intent_category': answer_intent_0_category,
                        'answer-summary': answer.get('summary', {}).get('text', ''),
                        'answer-summary_wordCount': answer.get('summary', {}).get('wordCount', ''),
                        
                        # question_audio
                        'question_audio-fileFormat': raw_data_info.get('question', {}).get('fileFormat', ''),
                        'question_audio-fileSize': raw_data_info.get('question', {}).get('fileSize', ''),
                        'question_audio-duration': raw_data_info.get('question', {}).get('duration', ''),
                        'question_audio-samplingBit': raw_data_info.get('question', {}).get('samplingBit', ''),
                        'question_audio-channelCount': raw_data_info.get('question', {}).get('channelCount', ''),
                        'question_audio-samplingRate': raw_data_info.get('question', {}).get('samplingRate', ''),
                        'question_audio-audioPath': raw_data_info.get('question', {}).get('audioPath', ''),
                        
                        # answer_audio
                        'answer_audio-fileFormat': raw_data_info.get('answer', {}).get('fileFormat', ''),
                        'answer_audio-fileSize': raw_data_info.get('answer', {}).get('fileSize', ''),
                        'answer_audio-duration': raw_data_info.get('answer', {}).get('duration', ''),
                        'answer_audio-samplingBit': raw_data_info.get('answer', {}).get('samplingBit', ''),
                        'answer_audio-channelCount': raw_data_info.get('answer', {}).get('channelCount', ''),
                        'answer_audio-samplingRate': raw_data_info.get('answer', {}).get('samplingRate', ''),
                        'answer_audio-audioPath': raw_data_info.get('answer', {}).get('audioPath', '')
                    }
                    
                    writer.writerow(row)
                    success_count += 1
                    
                    # 진행 상황 표시 (매 100개마다)
                    if idx % 100 == 0:
                        print(f"  처리 중: {idx}/{len(data)} ({idx/len(data)*100:.1f}%)")
                    
                except Exception as e:
                    error_count += 1
                    print(f"  ✗ 오류 (항목 {idx}): {e}")
            
            print(f"  처리 완료: {len(data)}/{len(data)} (100.0%)")
        
        # 파일 크기 확인
        file_size = Path(csv_file).stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        print("\n" + "=" * 70)
        print("✅ 변환 완료!")
        print("=" * 70)
        print(f"\n📊 통계:")
        print(f"  - 성공: {success_count}개")
        print(f"  - 실패: {error_count}개")
        print(f"  - 총 데이터: {len(data)}개")
        print(f"  - 총 컬럼: {len(headers)}개")
        print(f"\n📁 출력 파일:")
        print(f"  - 경로: {csv_file}")
        print(f"  - 크기: {file_size_mb:.2f} MB ({file_size:,} bytes)")
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ CSV 파일 생성 실패: {e}")

def main():
    # Train 데이터 변환
    train_json = Path(r"C:\dev\study\4th_mini_project\dataset\training\train_merged_all.json")
    train_csv = Path(r"C:\dev\study\4th_mini_project\dataset\train_detailed_all.csv")
    
    if train_json.exists():
        flatten_json_to_csv(train_json, train_csv)
    else:
        print(f"❌ JSON 파일을 찾을 수 없습니다: {train_json}")
    
    # Valid 데이터 변환
    print("\n\n")
    valid_json = Path(r"C:\dev\study\4th_mini_project\dataset\valid\valid_merged_all.json")
    valid_csv = Path(r"C:\dev\study\4th_mini_project\dataset\valid_detailed_all.csv")
    
    if valid_json.exists():
        flatten_json_to_csv(valid_json, valid_csv)
    else:
        print(f"❌ JSON 파일을 찾을 수 없습니다: {valid_json}")

if __name__ == "__main__":
    main()