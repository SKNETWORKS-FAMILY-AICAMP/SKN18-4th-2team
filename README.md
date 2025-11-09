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
│       │   ├── model/              # OpenAI 모델 팩토리 및 유틸
│       │   ├── retrieval/          # pgvector 연결, 검색 쿼리, 평가
│       │   └── workflow/           # LangGraph 상태/노드/그래프 실행
│       └── database/               # 원본 데이터 & 전처리
│           ├── college/            # 학과 관련 CSV/JSON
│           ├── interview/          # 면접 QA CSV
│           └── data_preprocess/    # JSON→CSV 변환 스크립트
├── docker/                         # pgvector docker-compose + init.sql
│   ├── docker-compose.yml
│   ├── init.sql
│   └── data/                       # Postgres 데이터 볼륨
├── imagelanggraph.ipynb            # LangGraph 구조 시각화 노트북
├── requirements.txt                # Python 의존성
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
