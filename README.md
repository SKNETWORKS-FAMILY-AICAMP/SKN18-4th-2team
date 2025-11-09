# SKN18-4th-2team

## Repository Layout
```
.
├── backend/
│   ├── django/                     # Django 프로젝트 루트
│   │   ├── config/                 # settings, urls, asgi, wsgi
│   │   └── manage.py
│   └── service/                    # 모델/그래프/데이터 파이프라인
│       ├── common/                 # 공통 로직
│       │   ├── embedding/          # 임베딩 생성 및 검색
│       │   │   ├── embed_data.py       # 데이터 임베딩 생성
│       │   │   ├── search_similar.py   # 유사도 검색
│       │   │   └── embedding.md        # 임베딩 관련 문서
│       │   ├── model/              # LLM 모델 팩토리 및 유틸
│       │   │   ├── models.py           # 모델 인스턴스 생성
│       │   │   └── utils.py            # 모델 관련 유틸리티
│       │   ├── retrieval/          # Vector DB 연결 및 관리
│       │   │   └── vectorstore/
│       │   │       ├── create_vectordb.py  # VectorDB 생성 파이프라인
│       │   │       └── vectordb/
│       │   │           ├── connect_db.py   # PostgreSQL 연결
│       │   │           ├── data_loader.py  # CSV 데이터 로더
│       │   │           ├── pgvector.py     # pgvector 테이블 관리
│       │   │           ├── Singleton.py    # DB 커넥션 풀 싱글톤
│       │   │           └── splitter.py     # 텍스트 청킹
│       │   └── workflow/           # LangGraph 워크플로우
│       │       ├── agents/             # 외부 API/LLM 래퍼
│       │       ├── graph/              # 그래프 빌더
│       │       │   └── graph_builder.py
│       │       ├── nodes/              # 그래프 노드
│       │       │   └── classify.py
│       │       └── states/             # 상태 정의
│       │           ├── graph_state.py
│       │           ├── interview_state.py
│       │           └── college_state.py
│       └── database/               # 원본 데이터 & 전처리
│           ├── college/            # 학과 데이터
│           │   ├── majors_with_chunks.csv      # 청킹된 학과 정보
│           │   └── major_universities.csv      # 학과-대학 매핑
│           ├── interview/          # 면접 데이터셋
│           │   ├── interview_final_dataset.csv # 최종 면접 데이터
│           │   ├── interview_sft_chatml.jsonl  # SFT용 데이터
│           │   ├── make_ft_jsonl.py            # JSONL 변환 스크립트
│           │   ├── valid_merged_all_preprocessed.csv
│           │   └── gemma_lora.ipynb            # LoRA 파인튜닝 노트북
│           └── data_preprocess/    # 전처리 스크립트
│               ├── college/            # 학과 데이터 전처리
│               │   ├── export_to_csv.py
│               │   ├── major_details_공학.json
│               │   ├── major_details_의약.json
│               │   └── major_details_자연.json
│               └── interview/          # 면접 데이터 전처리
│                   ├── data_preprocessiong.md      # 전처리 파이프라인 문서
│                   ├── unzip_and_merge.py          # ZIP 압축 해제 및 병합
│                   ├── merge_json.py               # JSON 병합
│                   ├── json_to_csv_detailed.py    # JSON→CSV 변환
│                   ├── check_columns.py            # 데이터 품질 검증
│                   ├── drop_columns.py             # 컬럼 제거
│                   ├── merge_csv.py                # CSV 병합
│                   ├── filter_experienced.py       # EXPERIENCED 필터링
│                   ├── add_sample_id.py            # Sample ID 추가
│                   ├── run_intent_tagger_v3.py     # Intent 태깅
│                   ├── prepare_interview_dataset.py
│                   └── valid_merged_all.csv
├── docker/                         # PostgreSQL + pgvector 환경
│   ├── docker-compose.yml          # Docker Compose 설정
│   ├── vector_init.sql             # pgvector 초기화 스크립트
│   ├── meta_queries.sql            # 메타 쿼리
│   └── sql_detail.md               # SQL 상세 문서
├── imagelanggraph.ipynb            # LangGraph 구조 시각화 노트북
├── requirements.txt                # Python 의존성
├── .env.sample                     # 환경변수 샘플
└── README.md
```

## 각 파일 별 설명 및 역할

| 파일 | 설명 |
| --- | --- |
| `create_vectordb.py` | 파이프라인 진입점. `.env` 로드 → DB 연결 → CSV 로딩 → `split_chunk_rows` 로 청크 분할 → 임베딩 생성 및 upsert → 대학 매핑 테이블 적재까지 순차 실행. 상단의 `BATCH_SIZE`, `CHUNK_SIZE`, `CHUNK_OVERLAP` 상수로 배치/청킹 전략을 빠르게 조정 가능. |
| `vectordb/connect_db.py` | `.env` 의 Postgres 설정을 읽어 `SingletonDatabase` 풀을 생성. DSN/호스트 기반 모두 지원, `minconn/maxconn` 값을 환경변수로 제어할 수 있게 분리. |
| `vectordb/Singleton.py` | psycopg2 `SimpleConnectionPool` 을 래핑한 단일톤 구현. pgvector 갱신 시 커넥션을 재사용, 매 호출마다 `register_vector` 를 바인딩. |
| `vectordb/data_loader.py` | `backend/service/database/college` 내 CSV를 읽어오는 헬퍼. 경로 검증, CSV→dict 리스트 변환, 배치 슬라이싱(`iter_batches`) 을 담당. |
| `vectordb/splitter.py` | `RecursiveCharacterTextSplitter` 를 통해 각 row 의 `chunk_text` 를 런타임에 잘게 split함. 새 청크마다 `chunk_index` 를 채워 넣어 중복 없이 upsert 할 수 있게 준비. |
| `vectordb/pgvector.py` | pgvector 테이블(upsert SQL)과 `major_universities` 보조 테이블을 직접 관리. 임베딩 벡터/metadata 를 묶어 insert 하고 `chunk_index` 를 키에 포함시켜 동일 필드에서도 여러 청크를 관리. |


### 실행 순서
루트 dir 기준으로 밑에 명령어 순서대로 실행

```bash
# 1. Postgres/pgvector 컨테이너 기동 후 healthy 상태까지 대기
docker compose --env-file .env -f docker/docker-compose.yml up -d --wait

# 2. CSV → 청킹 → 임베딩 → pgvector upsert
python -m backend.service.common.retrieval.vectorstore.create_vectordb
```

`docker compose --env-file .env -f docker/docker-compose.yml ps` , `docker ps --filter name=pgvector_db` 는 도커 Healthy 상태 체크를 위한 명령어

## Workflow 예시


```
backend/service/common/workflow/
├── states/
│   └── graph_state.py          # 시나리오·질문·retrieval 결과 등을 담는 공용 상태
├── agents/                     # 외부 LLM/DB/API 래퍼
│   ├── classify_agent.py       # 시나리오 라우터
│   ├── question_agent.py
│   ├── interview_rag_agent.py
│   ├── interview_ft_agent.py
│   ├── interview_eval_agent.py
│   ├── college_rdb_agent.py
│   ├── college_vectordb_agent.py
│   ├── tavily_agent.py
│   └── college_eval_agent.py
├── nodes/                      # LangGraph 노드 (상태 업데이트 + agent 호출)
│   ├── classify_node.py
│   ├── question_node.py
│   ├── interview_retrieve_node.py
│   ├── interview_eval_node.py
│   ├── interview_generate_node.py
│   ├── college_retrieve_node.py
│   ├── college_eval_node.py
│   └── college_generate_node.py
└── graph/
    └── builder.py              # StateGraph 정의, 조건부 edge, fallback 경로
```

- **states**: `GraphState` 데이터 구조로 시나리오, 질문, retriever 결과, retry 횟수 등을 관리.
- **agents**: 실제 LLM이나 DB, Tavily API 호출을 캡슐화하는 모듈.
- **nodes**: LangGraph에서 연결되는 함수. 각 노드가 적절한 agent를 호출하고 state를 갱신/분기.
- **graph/builder.py**: `StateGraph(GraphState)` 를 구성하고 `add_conditional_edges` 로 면접/대학 플로우 및 fallback 루프를 정의.
