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
