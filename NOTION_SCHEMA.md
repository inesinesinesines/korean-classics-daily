# Notion Database Schema

`push_to_notion.py`가 쓰는 Notion DB를 만들 때 필요한 속성 목록입니다.
Notion에서 새 DB를 만든 뒤 아래 속성을 그대로 추가하세요. 이름과 타입이 반드시 일치해야 합니다.

| 속성 이름 | 타입 | 비고 |
|---|---|---|
| Name | Title | 기본 타이틀 (자동 생성됨) |
| Date | Date | 리포트 날짜 |
| Book ID | Number | books.json의 id와 매칭 |
| Author | Rich text | 작자 (작자미상 포함) |
| Title | Rich text | 작품명 |
| Category | Select | 고전소설 / 고전시가 / 가사 / 고전수필 |
| Subgenre | Select | 판소리계소설 / 한문단편 / 향가 / 고려가요 / 연시조 / 기행가사 / 설(說) 등 |
| Period | Select | 통일신라 / 고려 / 조선전기 / 조선중기 / 조선후기 / 백제 등 |
| Source Rank | Number | 1(핵심)~4(외부) |
| Source Basis | Rich text | 출제·수록 근거 |
| Reading Mode | Select | ranked / strict / extended |
| One-line Summary | Rich text | 한 줄 요약 |
| Full Summary | Rich text | 전체 내용 요약 (5~6문장 병합) |
| Literary Significance | Rich text | 문학사적 의의와 특징 |
| Interpretations | Rich text | 여러 해석 요약 (관점 + 설명 병합) |
| Keywords | Multi-select | 핵심 키워드 |
| Discussion Question | Rich text | 토론 질문 |
| JSON URL | URL | GitHub Pages의 daily JSON 링크 |
| Web App URL | URL | 웹앱 배포 URL |

## 생성 절차

1. Notion에서 새 DB(Full page) 생성
2. 위 속성을 모두 추가 (대소문자·띄어쓰기 일치 필수)
3. Integration 연결: https://www.notion.so/my-integrations 에서 새 internal integration 만들고,
   해당 DB 페이지 우측 상단 `Connections`에 추가
4. DB URL에서 database_id 추출 (`notion.so/{workspace}/{id}?v=...` 형태에서 하이픈 제거한 32자)
5. `.env` 또는 GitHub Actions secrets에 다음 설정:
   - `NOTION_API_KEY=secret_...`
   - `NOTION_DATABASE_ID=<32자 id>`

## Select 옵션 시드값

미리 만들어 두면 첫 push 시 자동 생성 대기 시간을 줄일 수 있습니다.

- Category: 고전소설, 고전시가, 가사, 고전수필
- Subgenre: 전기소설, 몽자류소설, 판소리계소설, 영웅·군담소설, 가정소설, 한문단편, 우화소설, 애정소설, 풍자소설, 향가(4구체), 향가(8구체), 향가(10구체), 고려가요, 백제가요, 평시조, 연시조, 사설시조, 한시(5언절구), 한시(7언절구), 한시(7언고시), 양반가사·강호가사, 기행가사, 연군가사, 은일가사, 전쟁가사, 내방가사·규방가사, 월령체가사, 유배가사, 설(說), 기(記)·기행문, 제문, 내간체수필·우화, 궁정수필·회고록
- Period: 백제, 신라, 통일신라, 고려, 고려말·조선초, 조선전기, 조선중기, 조선후기
- Reading Mode: ranked, strict, extended
