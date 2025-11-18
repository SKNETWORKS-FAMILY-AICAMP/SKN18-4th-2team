# LLM Fine-tuning 가이드

이 폴더는 **Gemma-3-1B** 모델을 진로 상담 도메인에 맞게 파인튜닝하는 과정을 담고 있습니다.

## 📁 파일 구조

```
LLM_finetunig/
├── gemma31b-final.ipynb          # 파인튜닝 전체 프로세스 노트북
├── real_final_counseling.jsonl   # 진로 상담 학습 데이터셋 (5,046개 샘플)
└── README.md                     # 본 문서
```

## 🎯 목적

**진로·심리 상담사** 역할을 수행하는 LLM을 학습시켜, 대학 진로 상담 파이프라인에서 RAG 대신 파인튜닝 모델을 사용할 수 있도록 합니다.

## 📊 데이터셋

### `real_final_counseling.jsonl`

- **형식**: JSONL (JSON Lines)
- **구조**: ChatML 형식의 대화 데이터
- **샘플 수**: 5,046개
- **포맷**:
  ```json
  {
    "messages": [
      {
        "role": "system",
        "content": "당신은 공감적이고 실질적인 진로·심리 상담사입니다..."
      },
      {
        "role": "user",
        "content": "최근 친구들이 자신이 좋아하는 것과 잘하는 것을 발견해..."
      },
      {
        "role": "assistant",
        "content": "자신의 특성 파악은 진로선택의 가장 기본적인 토대가 되기 때문에..."
      }
    ]
  }
  ```

### 데이터 특징

- **도메인**: 진로 상담, 심리 상담, 대학 진학 상담
- **스타일**: 공감적이고 실질적인 조언 제공
- **주제 예시**:
  - 진로 선택 고민
  - 좋아하는 것 vs 잘하는 것의 차이
  - 꿈이 없는 상황에서의 진로 탐색
  - 부모님과의 진로 갈등
  - 특수중학교 진학 상담

## 🔧 기술 스택

### 모델
- **Base Model**: `google/gemma-3-1b-it` (Instruction-tuned 버전)
- **파인튜닝 방법**: LoRA (Low-Rank Adaptation)
- **양자화**: 4-bit (BitsAndBytesConfig)

### 라이브러리
- `transformers`: 모델 로딩 및 학습
- `peft`: LoRA 구현
- `trl`: SFTTrainer (Supervised Fine-Tuning)
- `datasets`: 데이터셋 처리
- `bitsandbytes`: 양자화 지원

## 📝 학습 프로세스

### 1. 환경 설정
```python
# 필수 패키지 설치
!pip install transformers accelerate bitsandbytes sentencepiece peft datasets trl
```

### 2. 모델 로딩
- **4-bit 양자화**로 메모리 효율성 확보
- `use_fast=False` (Gemma-3 토크나이저 버그 대응)
- `pad_token = eos_token` 설정

### 3. 데이터 전처리
- **ChatML 형식 변환**: Gemma-3 공식 포맷
  ```
  <start_of_turn>system
  {system_content}
  <end_of_turn>
  <start_of_turn>user
  {user_content}
  <end_of_turn>
  <start_of_turn>assistant
  {assistant_content}
  <end_of_turn>
  ```
- **텍스트 정제**: HTML 태그 제거, 공백 정규화
- **토크나이징**: `max_length=2048`, `token_type_ids` 생성

### 4. LoRA 설정
```python
LoraConfig(
    r=32,                    # rank (1B 모델은 16~32 추천)
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ]
)
```

### 5. 학습 설정
```python
SFTConfig(
    num_train_epochs=10,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,  # 실제 batch size = 8
    learning_rate=2e-4,
    bf16=True,
    optim="paged_adamw_32bit"
)
```

### 6. Early Stopping
- **CustomEarlyStopping** 콜백 구현
- `patience=10`, `min_delta=0.001`
- Train loss 기반으로 학습 조기 종료

## 🚀 실행 방법

### 노트북 실행
1. Google Colab 또는 로컬 Jupyter 환경에서 `gemma31b-final.ipynb` 열기
2. HuggingFace 로그인 (모델 다운로드용)
3. 셀 순서대로 실행

### 주요 단계
1. **셀 0-3**: 패키지 설치 및 환경 설정
2. **셀 4**: Base 모델 다운로드 및 저장
3. **셀 5-7**: 데이터셋 로드 및 전처리
4. **셀 8**: Data Collator 설정 (Gemma-3 호환)
5. **셀 9**: LoRA 설정
6. **셀 10-11**: Trainer 설정 및 학습 시작
7. **셀 12**: `trainer.train()` 실행
8. **셀 13**: 파인튜닝된 모델 저장
9. **셀 14-15**: HuggingFace Hub 업로드 (선택)
10. **셀 16-18**: 모델 로드 및 추론 테스트

## 💾 모델 저장

### 로컬 저장
- **경로**: `gemma3_lora_output4/` 또는 `gemma3_lora_college2/`
- **포함 파일**:
  - `adapter_config.json`
  - `adapter_model.safetensors`
  - `tokenizer_config.json`
  - `tokenizer.json`

### HuggingFace Hub 업로드
```python
from huggingface_hub import HfApi

api = HfApi()
api.upload_folder(
    repo_id="your-username/gemma3-finetuned-counseling",
    folder_path="gemma3_lora_output4",
    commit_message="Upload finetuned LoRA model"
)
```

## 🔍 추론 사용법

### 파인튜닝 모델 로드
```python
from peft import PeftModel

base_model = AutoModelForCausalLM.from_pretrained(
    "google/gemma-3-1b-it",
    quantization_config=bnb_config,
    device_map="auto"
)

ft_model = PeftModel.from_pretrained(
    base_model,
    "gemma3_lora_output4"  # 로컬 경로 또는 HF Hub ID
)
```

### 추론 실행
```python
def infer_ft(query):
    ft_model.eval()
    inp = tokenizer(query, return_tensors="pt").to(ft_model.device)
    
    out = ft_model.generate(
        input_ids=inp["input_ids"],
        attention_mask=inp.get("attention_mask"),
        max_new_tokens=200
    )
    
    return tokenizer.decode(out[0], skip_special_tokens=True)
```

## 📈 학습 결과

- **학습 데이터**: 5,046개 샘플
- **Trainable Parameters**: 26,091,520 (LoRA 어댑터만)
- **Total Batch Size**: 8 (per_device=2 × gradient_accumulation=4)
- **Total Steps**: 6,310 (10 epochs 기준)

## ⚙️ 하이퍼파라미터 튜닝 가이드

### LoRA Rank (r)
- **1B 모델**: 16~32 추천
- **더 큰 모델**: 64~128 가능
- **메모리 vs 성능**: rank가 클수록 더 많은 파라미터 학습, 더 나은 성능 가능

### Learning Rate
- **기본값**: 2e-4
- **조정 범위**: 1e-4 ~ 5e-4
- **너무 높으면**: 불안정한 학습, loss 발산
- **너무 낮으면**: 학습 속도 저하

### Batch Size
- **메모리 제약**: `per_device_train_batch_size=2`
- **실제 배치**: `gradient_accumulation_steps=4`로 총 8
- **GPU 메모리 부족 시**: `gradient_accumulation_steps` 증가

## 🐛 주의사항

1. **토크나이저 버그**: `use_fast=False` 필수
2. **token_type_ids**: Gemma-3는 지원하지 않지만, 학습 시 생성 필요
3. **양자화**: 4-bit 사용 시 추론 속도 향상, 정확도 약간 저하 가능
4. **Early Stopping**: Overfitting 방지를 위해 patience 조정 권장

## 🔗 관련 파일

- **데이터 생성**: `backend/embedding/make_finetune_dataset.py`
- **LangGraph 통합**: `backend/LangGraph/nodes/classify_rag_finetune.py`
- **모델 사용**: `backend/service/main.py`

## 📚 참고 자료

- [Gemma-3 모델 카드](https://huggingface.co/google/gemma-3-1b-it)
- [PEFT LoRA 문서](https://huggingface.co/docs/peft/conceptual_guides/lora)
- [TRL SFTTrainer 문서](https://huggingface.co/docs/trl/sft_trainer)

