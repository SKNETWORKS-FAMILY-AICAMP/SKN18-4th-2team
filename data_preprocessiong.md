# 데이터 전처리 파이프라인 (Data Preprocessing Pipeline)

## 📋 개요
이 문서는 `data_preprocessiong` 폴더의 Python 스크립트들의 기능과 사용 순서를 설명합니다.

---

## 🔄 전처리 순서 및 스크립트 기능

### 1단계: `unzip_and_merge.py`
**기능**: ZIP 파일 압축 해제 및 병합

- **주요 작업**:
  - 지정된 디렉토리 내의 모든 `.zip` 파일을 압축 해제
  - 압축 해제된 각 폴더의 내용을 하나의 디렉토리로 병합
  - 상대 경로 구조를 유지하면서 파일 복사

- **입력**: 
  - `C:\dev\study\4th_mini_project\SKN18-4th-2team\backend\service\database\data_preprocess\interview\rag` (또는 valid)
  
- **출력**: 
  - `training_extracted\` (압축 해제된 중간 파일)
  - `training_merged\` (병합된 데이터)

- **주요 함수**:
  - `extract_zip_files()`: ZIP 파일 압축 해제
  - `merge_extracted_data()`: 압축 해제된 데이터 병합

---

### 2단계: `merge_json.py`
**기능**: 여러 JSON 파일을 하나의 JSON 파일로 병합

- **주요 작업**:
  - 디렉토리 내의 모든 JSON 파일 검색
  - 각 JSON 파일을 읽어 하나의 리스트로 병합
  - 단일 JSON 파일로 저장

- **입력**: 
  - `train_merged/` 또는 `valid_merged/` 디렉토리의 JSON 파일들
  
- **출력**: 
  - `train_merged_all.json`
  - `valid_merged_all.json`

- **특징**:
  - 100개 단위로 진행 상황 표시
  - UTF-8 인코딩, indent=2로 가독성 있게 저장

---

### 3단계: `json_to_csv_detailed.py`
**기능**: JSON 파일을 평면화하여 CSV로 변환

- **주요 작업**:
  - JSON 계층 구조를 평면화
  - 총 38개 컬럼으로 구조화
  - emotion, intent 정보를 JSON 문자열 및 개별 필드로 분리

- **입력**: 
  - `train_merged_all.json`
  - `valid_merged_all.json`
  
- **출력**: 
  - `train_detailed_all.csv`
  - `valid_detailed_all.csv`

- **주요 컬럼 카테고리**:
  - **version**: 데이터 버전
  - **info**: 날짜, 직업, 채널, 장소, 성별, 연령대, 경험
  - **question**: 질문 텍스트, 단어 수, 감정, 의도
  - **answer**: 답변 텍스트, 감정, 의도, 요약
  - **audio**: 질문/답변 오디오 메타데이터

---

### 4단계: `check_columns.py`
**기능**: CSV 파일의 컬럼 데이터 품질 확인

- **주요 작업**:
  - `question-emotion`, `question-intent` 컬럼의 결측치 확인
  - 빈 값(`[]` 또는 빈 문자열) vs 값 있음 통계 출력

- **입력**: 
  - `train_detailed.csv`
  - `valid_detailed.csv`

- **출력**: 
  - 콘솔 출력 (통계 정보)

- **용도**: 데이터 품질 검증 및 다음 단계 처리 여부 결정

---

### 5단계: `drop_columns.py`
**기능**: 불필요한 컬럼 제거

- **주요 작업**:
  - 분석에 불필요한 27개 컬럼 제거
  - 필수 컬럼만 남긴 경량화된 CSV 생성

- **입력**: 
  - `train_detailed_all.csv`
  - `valid_detailed_all.csv`
  
- **출력**: 
  - `train_cleaned_all.csv`
  - `valid_cleaned_all.csv`

- **제거되는 컬럼 종류**:
  - version, date, channel, place
  - question-wordCount, question-emotion, question-intent
  - answer 관련 상세 정보 (emotion, intent 원본, wordCount 등)
  - 오디오 메타데이터 전체 (fileFormat, fileSize, duration 등)

- **남은 주요 컬럼**:
  - occupation, gender, ageRange, experience
  - question, answer
  - answer-emotion_expression, answer-emotion_category
  - answer-intent_category

---

### 6단계: `merge_csv.py`
**기능**: Train과 Valid CSV 파일 병합

- **주요 작업**:
  - Train과 Valid 데이터를 하나의 CSV로 통합
  - 헤더 일치 여부 확인 (불일치 시 공통 컬럼만 사용)
  - 데이터 통계 출력

- **입력**: 
  - `train_cleaned_all.csv`
  - `valid_cleaned_all.csv`
  
- **출력**: 
  - `merged_all.csv`

- **특징**:
  - Train + Valid 순서로 행 결합
  - 컬럼 불일치 시 경고 및 공통 컬럼만 사용

---

### 7단계: `filter_experienced.py`
**기능**: EXPERIENCED 데이터 필터링 및 Sample ID 부여

- **주요 작업**:
  1. `experience` 컬럼이 "EXPERIENCED"인 행만 추출
  2. `sample_id` 컬럼을 첫 번째 컬럼으로 추가 (1부터 시작)
  3. 컬럼별 결측치 통계 분석

- **입력**: 
  - `merged_all.csv`
  
- **출력**: 
  - `merged_experienced.csv`

- **결측치 분석**:
  - 각 컬럼별 결측치 수, 비율, 유효 데이터 수
  - 결측치가 있는 컬럼만 표시
  - 전체 통계 요약 (총 행/컬럼 수, 전체 결측치 수)

---

### 8단계: `add_sample_id.py`
**기능**: CSV 파일에 고유 Sample ID 추가

- **주요 작업**:
  - `sample_id` 컬럼을 첫 번째 컬럼으로 추가
  - 1부터 시작하는 일련번호 부여

- **입력**: 
  - `train_cleaned.csv` 또는 `valid_cleaned.csv`
  
- **출력**: 
  - 동일 파일명 (덮어쓰기)

- **특징**:
  - 데이터 추적 및 식별을 위한 고유 ID 생성

---

### 9단계: `run_intent_tagger_v3.py`
**기능**: 질문 텍스트에서 의도(Intent) 자동 태깅

- **주요 작업**:
  - 정규표현식 기반의 16가지 의도 카테고리 자동 분류
  - `question` 컬럼 분석하여 `question_intent` 컬럼 생성
  - 의도 분포 통계 출력

- **입력**: 
  - CSV 파일 (최소한 `question` 컬럼 필요)
  
- **출력**: 
  - `merged_experienced_with_question_intent.csv`

- **16가지 의도 카테고리** (우선순위 순):
  1. **motivation_fit**: 목표/지원동기/선호/희망부서
  2. **self_reflection**: 후회/장단점/자기소개/자신있는
  3. **criteria_evaluation**: 중요하게 생각/기준/평가척도
  4. **stakeholder_comm**: 협업/갈등/커뮤니케이션/조율
  5. **behavioral_star**: 경험/사례/극복/성과/결과
  6. **procedure_method**: 어떻게/방법/절차/프로세스
  7. **mechanism_reason**: 왜/이유/원인/소감/원리
  8. **compare_tradeoff**: 비교/장단점/vs/trade-off
  9. **evidence_metric**: 지표/수치/실험/검증/AUC/F1
  10. **leadership_ownership**: 리더십/오너십/주도/책임
  11. **creativity_ideation**: 창의/개선/아이디어
  12. **root_cause**: 원인분석/재발방지/디버그
  13. **ethics_compliance**: 윤리/준법/IRB/GDPR/개인정보
  14. **application_transfer**: 적용/현장/전이/실무적용
  15. **estimation_planning**: 대략/예상/일정/계획
  16. **cost_resource**: 비용/ROI/예산/원가/효율

- **사용법**:
  ```bash
  python run_intent_tagger_v3.py --input merged_experienced.csv --outdir ./output
  ```

- **알고리즘**:
  - 각 질문 텍스트를 소문자로 변환
  - 우선순위 순서대로 정규표현식 매칭
  - 첫 번째 매칭된 카테고리를 할당
  - 매칭되지 않으면 `mechanism_reason` (fallback)

---

## 📊 데이터 흐름 다이어그램

```
[ZIP 파일들]
    ↓
[1. unzip_and_merge.py]
    ↓
[JSON 파일들 (merged)]
    ↓
[2. merge_json.py]
    ↓
[단일 JSON 파일]
    ↓
[3. json_to_csv_detailed.py]
    ↓
[상세 CSV (38개 컬럼)]
    ↓
[4. check_columns.py] ← 데이터 품질 확인
    ↓
[5. drop_columns.py]
    ↓
[정제된 CSV (11개 컬럼)]
    ↓
[6. merge_csv.py]
    ↓
[병합된 CSV (train+valid)]
    ↓
[7. filter_experienced.py]
    ↓
[EXPERIENCED 데이터 + sample_id]
    ↓
[9. run_intent_tagger_v3.py]
    ↓
[최종 데이터 (question_intent 포함)]
```

---

## 🎯 주요 특징

### 인코딩 처리
- 모든 스크립트에서 **UTF-8-sig** 인코딩 사용
- 한글 데이터 손실 방지

### 진행 상황 표시
- 대용량 데이터 처리 시 100개 단위로 진행률 출력
- 성공/실패 건수 분리 집계

### 에러 핸들링
- try-except 블록으로 개별 레코드 오류 처리
- 전체 프로세스는 계속 진행

### 통계 정보 제공
- 각 단계마다 처리된 데이터 수, 파일 크기, 컬럼 수 등 출력
- 데이터 품질 및 결과 검증 용이

---

## ⚙️ 실행 권장 사항

1. **순차 실행**: 위의 순서대로 1~9단계 실행
2. **중간 확인**: 4단계(check_columns.py)에서 데이터 품질 확인
3. **백업**: 각 단계 후 중간 결과물 백업 권장
4. **경로 수정**: 각 스크립트의 경로는 프로젝트 환경에 맞게 수정 필요
5. **파일 크기**: 대용량 파일 처리 시 충분한 디스크 공간 확보

---

## 📁 최종 산출물

- **merged_experienced_with_question_intent.csv**
  - EXPERIENCED 데이터만 필터링
  - sample_id 포함
  - question_intent 자동 태깅 완료
  - 분석 및 모델링에 바로 사용 가능한 정제된 데이터

---

## 🔧 의존성

- **Python 3.x**
- **표준 라이브러리**: 
  - `os`, `zipfile`, `shutil`, `pathlib`, `json`, `csv`, `re`, `argparse`
- **외부 라이브러리**: 
  - `pandas` (run_intent_tagger_v3.py만 필요)

---

## 📝 참고사항

- `data_preprocessiong` 폴더명은 오타로 보이나 실제 폴더명 그대로 사용
- 일부 스크립트는 주석 처리된 코드 포함 (train/valid 개별 처리 옵션)
- 경로는 절대 경로 사용 (Windows 환경 기준)
