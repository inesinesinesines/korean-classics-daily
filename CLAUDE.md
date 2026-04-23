# Korean Classics Daily — Project Instructions

## Product Summary
수능 기출 + EBS 연계 한국 고전 문학 1편을 매일 자동 선택해 Claude API로 리포트(JSON)를 생성하고,
정적 웹(`index.html`) + Notion DB에 누적하는 서비스.
배포: GitHub Pages + GitHub Actions(`daily-update.yml`, `backfill.yml`).

자매 프로젝트: `great-books-daily` (서양 고전 100권 버전). 구조·관례 대부분 공유.

## Layout
```
books.json                     # 80편 한국 고전 마스터 (수능·EBS 기반)
data/today.json                # 오늘의 리포트
data/daily/{YYYY-MM-DD}.json   # 날짜별 리포트
generate_daily_report.py       # Claude API 호출 + JSON 저장
push_to_notion.py              # Notion DB 적재
run_daily.py                   # 위 2개 순차 실행
index.html                     # GitHub Pages 진입 페이지
.github/workflows/             # daily-update, backfill
NOTION_SCHEMA.md               # Notion DB 속성 설계 문서
```

## Report Schema (특징)

기존 great-books-daily 스키마에 **3가지 필드 추가**:

- `subgenre`, `period` — 장르/시대 메타
- `literary_significance` — 문학사적 의의와 특징 (200~300자)
- `interpretations` — 2~3개 관점, 각각 `{viewpoint, explanation, original_quote, quote_source}`

빠진 것:
- `why_now`, `tradition` 제거 (고전시가/가사와 충돌)

## Tech Stack
- Python 3.13 (anthropic, notion-client, python-dotenv — `requirements.txt`)
- 정적 프론트(바닐라 JS, 단일 `index.html`)
- GitHub Actions로 스케줄/백필

## Conventions
- 한국어 UX/본문 (코드 주석은 영문 가능)
- JSON은 `ensure_ascii=False`, 들여쓰기 2
- 루트 평탄 구조 유지
- 날짜/타임존은 `TIMEZONE`(기본 `Asia/Seoul`)

## 원문 인용 주의사항 (중요)

Claude가 한국 고전의 원문을 정확히 재현하기 어려운 경우가 많음. 프롬프트에서 강조:
- 확실한 짧은 대표 구절만 `original_quote`에 넣기
- 의심되면 빈 문자열("")
- 현대어 번역본/의역 금지
- 가짜 인용 엄금

사용자는 생성된 리포트의 원문 인용 정확성을 주기적으로 검토할 것.

## Key Env Vars
`ANTHROPIC_API_KEY`, `CLAUDE_MODEL`, `NOTION_API_KEY`, `NOTION_DATABASE_ID`,
`READING_MODE`(ranked|strict|extended), `TIMEZONE`, `START_DATE`, `WEB_APP_URL`, `JSON_BASE_URL`

## HALO Workflow
자매 프로젝트와 동일한 HALO Workflow v3 규약 사용 가능.
(필요 시 `.claude/commands/` 복사해서 활성화)

## Project-Specific Notes
- `src/` 레이아웃 쓰지 않음. Python은 루트, 프론트는 `index.html` 단일 파일
- 새 Python 모듈은 루트(또는 얕은 하위)에 둘 것
- GitHub Pages 정적 제약 기억 — 동적 기능은 Actions workflow_dispatch로
