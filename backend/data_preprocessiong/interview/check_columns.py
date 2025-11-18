import csv
from pathlib import Path

# Valid 파일 확인
print("=" * 70)
print("VALID 파일 확인")
print("=" * 70)
valid_csv = Path(r"C:\dev\study\4th_mini_project\dataset\ICT\valid_detailed.csv")

with open(valid_csv, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

emotion_empty = sum(1 for r in rows if r['question-emotion'] == '[]' or r['question-emotion'] == '')
emotion_has_value = sum(1 for r in rows if r['question-emotion'] != '[]' and r['question-emotion'] != '')
intent_empty = sum(1 for r in rows if r['question-intent'] == '[]' or r['question-intent'] == '')
intent_has_value = sum(1 for r in rows if r['question-intent'] != '[]' and r['question-intent'] != '')

print(f"\n📊 question-emotion: 빈 값 {emotion_empty}개, 값 있음 {emotion_has_value}개")
print(f"📊 question-intent: 빈 값 {intent_empty}개, 값 있음 {intent_has_value}개")

# Train 파일 확인
print("\n" + "=" * 70)
print("TRAIN 파일 확인")
print("=" * 70)
train_csv = Path(r"C:\dev\study\4th_mini_project\dataset\ICT\train_detailed.csv")

with open(train_csv, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

emotion_empty = sum(1 for r in rows if r['question-emotion'] == '[]' or r['question-emotion'] == '')
emotion_has_value = sum(1 for r in rows if r['question-emotion'] != '[]' and r['question-emotion'] != '')
intent_empty = sum(1 for r in rows if r['question-intent'] == '[]' or r['question-intent'] == '')
intent_has_value = sum(1 for r in rows if r['question-intent'] != '[]' and r['question-intent'] != '')

print(f"\n📊 question-emotion: 빈 값 {emotion_empty}개, 값 있음 {emotion_has_value}개")
print(f"📊 question-intent: 빈 값 {intent_empty}개, 값 있음 {intent_has_value}개")
