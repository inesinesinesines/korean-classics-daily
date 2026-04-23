# Korean Classics Daily

수능 기출 + EBS 연계 **한국 고전 문학**을 매일 한 편씩 Claude API로 리포트(JSON)화해서
정적 웹(GitHub Pages)과 Notion DB에 누적하는 서비스.

자매 프로젝트: [Great Books Daily](../great-books-daily) — 서양 고전 100권 버전.

## 구성

| 파일 | 역할 |
|---|---|
| `books.json` | 80편 한국 고전 마스터 (수능·모의평가·EBS 기반) |
| `generate_daily_report.py` | Claude API 호출 → `data/today.json`, `data/daily/{YYYY-MM-DD}.json` 생성 |
| `push_to_notion.py` | 생성된 리포트를 Notion DB에 upsert |
| `run_daily.py` | 위 두 스크립트를 순차 실행 |
| `index.html` | GitHub Pages 프론트엔드 |
| `.github/workflows/daily-update.yml` | 매일 03:20 UTC(= 12:20 KST) cron |
| `.github/workflows/backfill.yml` | 기간 지정 수동 백필 |
| `NOTION_SCHEMA.md` | Notion DB 속성 설계 |

## 리포트 스키마

```jsonc
{
  "date": "2026-04-24",
  "book_id": 1,
  "author": "김시습",
  "title": "만복사저포기",
  "category": "고전소설",
  "subgenre": "전기소설",
  "period": "조선전기",
  "source_rank": 1,
  "one_line": "한 줄 요약",
  "summary": ["전체 내용 요약 5~6문장"],
  "literary_significance": "문학사적 의의와 특징",
  "interpretations": [
    {
      "viewpoint": "주제론적 해석",
      "explanation": "…",
      "original_quote": "원문 구절",
      "quote_source": "『금오신화』 만복사저포기 중반부"
    }
  ],
  "keywords": ["…"],
  "discussion_question": "…",
  "next_recommendations": [ { "title": "...", "author": "...", "reason": "..." } ]
}
```

## 로컬 실행

```bash
python -m pip install -r requirements.txt
cp .env.example .env   # 값 채우기
python generate_daily_report.py              # 오늘치
python generate_daily_report.py 2026-04-24   # 특정 날짜
python generate_daily_report.py 3            # book_id=3 (홍길동전)
python push_to_notion.py                     # Notion 적재
```

## 환경 변수

| 이름 | 설명 |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API 키 |
| `CLAUDE_MODEL` | 기본 `claude-opus-4-7`, 비용 최적화 시 `claude-sonnet-4-6` |
| `NOTION_API_KEY` | Notion integration secret |
| `NOTION_DATABASE_ID` | Notion DB id (32자) |
| `READING_MODE` | `ranked`(기본) / `strict`(rank 1~2만) / `extended` |
| `TIMEZONE` | 기본 `Asia/Seoul` |
| `START_DATE` | 로테이션 기준일 (기본 `2026-04-24`) |
| `WEB_APP_URL` | 프론트 URL (Notion 연결용) |
| `JSON_BASE_URL` | 퍼블릭 JSON 베이스 URL |

## 커밋 규칙

- 한국어 UX/본문, 코드 주석은 영문 허용
- JSON은 `ensure_ascii=False`, 2-space indent
- 루트 평탄 구조 유지 (서브 디렉토리 금지)

## 주의: 원문 인용

프롬프트에서 강조: **정확하지 않은 원문 인용은 금지**.
Claude가 확실히 기억하는 짧은 대표 구절만 `original_quote`에 넣고,
의심되면 빈 문자열로 둡니다. 생성된 리포트를 검토할 때 원문 정확성 확인 필요.
