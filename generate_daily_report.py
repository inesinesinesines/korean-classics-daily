import json
import os
import re
import sys
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
# Defaults to Opus 4.7. Override via CLAUDE_MODEL env / Actions secret
# (e.g., claude-sonnet-4-6 for cheaper runs).
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL") or "claude-opus-4-7"
START_DATE = os.getenv("START_DATE", "2026-04-24")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Seoul")
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./data"))
BOOKS_PATH = Path(__file__).parent / "books.json"
READING_MODE = os.getenv("READING_MODE", "ranked").strip().lower()


def load_books(include_external: bool = False):
    """Load the curated Korean classics catalog.

    include_external=False (default) excludes source_rank>=4 entries so
    daily rotation is not polluted by user-added externals.
    """
    books = json.loads(BOOKS_PATH.read_text(encoding="utf-8"))
    if not include_external:
        books = [b for b in books if b.get("source_rank", 3) <= 3]
    if READING_MODE == "strict":
        return [b for b in books if b.get("source_rank", 3) <= 2]
    return books


def _normalize(s: str) -> str:
    return " ".join((s or "").strip().lower().split())


def add_external_book(title: str, author: str) -> dict:
    """Add or return an entry for a user-requested external Korean classic."""
    title = (title or "").strip()
    author = (author or "").strip()
    if not title or not author:
        raise ValueError("title and author are required for external book")

    books = json.loads(BOOKS_PATH.read_text(encoding="utf-8"))
    key = (_normalize(author), _normalize(title))
    for b in books:
        if (_normalize(b.get("author", "")), _normalize(b.get("title", ""))) == key:
            return b

    new_id = max((b.get("id", 0) for b in books), default=0) + 1
    entry = {
        "id": new_id,
        "author": author,
        "title": title,
        "category": "고전문학",
        "subgenre": "미상",
        "period": "미상",
        "source_rank": 4,
        "source_basis": "사용자 요청으로 추가된 외부 작품",
    }
    books.append(entry)
    BOOKS_PATH.write_text(
        json.dumps(books, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return entry


def get_today_local():
    return datetime.now(ZoneInfo(TIMEZONE)).date()


def pick_book(target_date: date, books: list[dict]) -> tuple[dict, int]:
    start = datetime.strptime(START_DATE, "%Y-%m-%d").date()
    delta = (target_date - start).days
    idx = delta % len(books)
    return books[idx], idx


def next_books(current_index: int, books: list[dict], count: int = 3) -> list[dict]:
    return [books[(current_index + i) % len(books)] for i in range(1, count + 1)]


def recommendation_reason(book: dict) -> str:
    rank = book.get("source_rank", 3)
    if rank == 1:
        return "수능·모의평가·EBS 연계에서 최다 출제된 핵심 작품입니다."
    if rank == 2:
        return "EBS 연계 및 기출에 꾸준히 수록되는 보완 작품입니다."
    return "작품 스펙트럼을 넓히는 확장 고전 단계의 작품입니다."


def build_prompt(book: dict, target_date: str, excluded_titles: list[str]) -> str:
    """Build Claude prompt. Schema: summary, literary_significance,
    interpretations (2~3, each with original_quote + quote_source)."""
    excluded_block = "\n".join(f"- {t}" for t in excluded_titles)
    return f"""
당신은 한국 고전 문학을 다루는 일일 리포트의 편집자입니다.
반드시 JSON만 반환하세요. 마크다운, 코드펜스, 설명 문장 없이 순수 JSON만 출력하세요.

날짜: {target_date}
읽기 모드: {READING_MODE}
오늘의 작품:
- id: {book['id']}
- author: {book['author']}
- title: {book['title']}
- category: {book['category']}
- subgenre: {book.get('subgenre', '')}
- period: {book.get('period', '')}
- source_rank: {book.get('source_rank', 3)}
- source_basis: {book.get('source_basis', '')}
- importance: {book.get('importance', '')}  (1~5)
- exam_count_sat: {book.get('exam_count_sat', '')}
- exam_count_mock: {book.get('exam_count_mock', '')}
- ebs_count: {book.get('ebs_count', '')}
- latest_year: {book.get('latest_year', '')}

이 앱에 이미 등록된 작품(아래 목록) 안의 텍스트는 next_recommendations 후보에서
**반드시 제외**하세요. 추천은 아래 목록에 없는 한국 고전이어야 합니다.

==== 제외 목록 (Author / Title) ====
{excluded_block}
==== 제외 목록 끝 ====

반환 JSON 스키마:
{{
  "date": "{target_date}",
  "book_id": {book['id']},
  "author": "{book['author']}",
  "title": "{book['title']}",
  "category": "{book['category']}",
  "subgenre": "{book.get('subgenre', '')}",
  "period": "{book.get('period', '')}",
  "source_rank": {book.get('source_rank', 3)},
  "source_basis": "{book.get('source_basis', '')}",
  "importance": {book.get('importance', 3)},
  "exam_count_sat": {book.get('exam_count_sat', 0)},
  "exam_count_mock": {book.get('exam_count_mock', 0)},
  "ebs_count": {book.get('ebs_count', 0)},
  "latest_year": "{book.get('latest_year', '')}",
  "reading_mode": "{READING_MODE}",
  "one_line": "한국어 한 문장 요약",
  "summary": ["문장1", "문장2", "문장3", "문장4", "문장5", "문장6"],
  "literary_significance": "문학사적 의의와 특징 — 장르·형식·주제 차원에서 이 작품이 한국문학사에서 차지하는 위치, 형식적 특징, 계승 관계 등을 200~300자 한국어로 서술",
  "interpretations": [
    {{
      "viewpoint": "관점 이름 (예: 주제론적 해석 / 형식·구조 분석 / 사회사적 해석 / 여성주의적 재독 등)",
      "explanation": "해당 관점의 핵심 주장을 2~3문장 한국어로",
      "original_quote": "원문 중 이 관점을 뒷받침하는 대표 구절 1개 (현대어 풀이가 아닌 원문 표기. 확실하지 않으면 빈 문자열)",
      "quote_source": "인용 구절의 출처 위치 (예: 『춘향전』 초반부 / 『관동별곡』 서사 / 1곡 초장 등)"
    }}
  ],
  "keywords": ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5"],
  "discussion_question": "한국어 토론 질문 1개",
  "perplexity_followup_prompt": "사용자가 Perplexity에 이어서 물을 수 있는 한국어 질문",
  "next_recommendations": [
    {{"title": "...", "author": "...", "reason": "...", "external": true}},
    {{"title": "...", "author": "...", "reason": "...", "external": true}},
    {{"title": "...", "author": "...", "reason": "...", "external": true}}
  ],
  "source_note": "수능 기출 + EBS 연계 한국 고전 일일 리포트"
}}

필수 요구사항:
- 자연스러운 한국어로, 고등 국어 학습자가 이해할 수 있는 수준으로 작성
- summary는 전체 내용(줄거리·화자의 정서·구조 흐름)을 빠짐없이 압축
- literary_significance는 “문학사적 위치 + 장르/형식적 특징 + 영향·계승”을 포함
- interpretations는 서로 다른 접근 방식 2~3개 (예: 주제론 / 형식·구조 / 사회사 / 수용사 등)
- **원문 인용(original_quote)은 반드시 실제 원문 표기를 따를 것.**
  확실히 기억나는 대표 구절만 짧게(1~2행) 인용하고, 정확도가 의심되면 빈 문자열("")로 둘 것.
  현대어 번역본이나 의역은 금지. 가짜 인용 엄금.
- quote_source는 인용 구절의 원문 위치를 구체적으로 명시 (편명/장면/몇 곡 몇 장 등)
- next_recommendations는 **위 제외 목록에 없는 실존 한국 고전** 3편. 같은 작가/장르/주제로 이어지는 작품을 고르고, reason은 2~3문장.
- JSON 외의 어떤 텍스트도 출력하지 말 것.
""".strip()


def extract_text(resp) -> str:
    parts = []
    for block in resp.content:
        text = getattr(block, 'text', None)
        if text:
            parts.append(text)
    return ''.join(parts).strip()


def strip_code_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        first_nl = text.index("\n")
        text = text[first_nl + 1:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def call_claude(prompt: str) -> dict:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError('ANTHROPIC_API_KEY is missing')
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    msg = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2800,
        messages=[{"role": "user", "content": prompt}],
    )
    content = extract_text(msg)
    content = strip_code_fences(content)
    return json.loads(content)


def fallback_report(book: dict, target_date: str, recommendations: list[dict]) -> dict:
    return {
        "date": target_date,
        "book_id": book["id"],
        "author": book["author"],
        "title": book["title"],
        "category": book["category"],
        "subgenre": book.get("subgenre", ""),
        "period": book.get("period", ""),
        "source_rank": book.get("source_rank", 3),
        "source_basis": book.get("source_basis", ""),
        "importance": book.get("importance", 3),
        "exam_count_sat": book.get("exam_count_sat", 0),
        "exam_count_mock": book.get("exam_count_mock", 0),
        "ebs_count": book.get("ebs_count", 0),
        "latest_year": book.get("latest_year", ""),
        "reading_mode": READING_MODE,
        "one_line": f"{book['author']}의 『{book['title']}』을(를) 오늘의 한국 고전으로 읽는 일일 리포트입니다.",
        "summary": [
            f"이 작품은 {book.get('period','')} 시기의 {book.get('subgenre', book['category'])} 계열에 속합니다.",
            "장르 특성과 구조, 화자의 태도를 중심으로 읽는 것이 좋습니다.",
            "핵심 갈등과 주제의식을 작품 전체의 흐름에서 파악해 보세요.",
            "문학사적 위치와 당대 수용사를 함께 살펴보면 이해가 깊어집니다.",
            "수능·EBS 연계에서 반복 출제되는 맥락을 고려해 읽어 보세요.",
            "오늘의 리포트는 다양한 해석 관점까지 간단히 연결해 줍니다."
        ],
        "literary_significance": "자동 생성 실패 시 임시 요약입니다. 장르적 전형성, 형식적 특징, 문학사적 계승 관계에 주목해 주세요.",
        "interpretations": [
            {
                "viewpoint": "주제론적 해석",
                "explanation": "작품의 핵심 주제와 시대적 문제의식을 중심에 두는 접근입니다.",
                "original_quote": "",
                "quote_source": ""
            },
            {
                "viewpoint": "형식·구조 분석",
                "explanation": "갈래의 관습과 구성적 장치가 의미를 어떻게 형성하는지 살피는 접근입니다.",
                "original_quote": "",
                "quote_source": ""
            }
        ],
        "keywords": [book["category"], book.get("subgenre", ""), book.get("period", ""), "주제", "형식"],
        "discussion_question": f"『{book['title']}』의 핵심 문제의식을 오늘의 관점에서 재해석하면 어떤 논점이 생길까?",
        "perplexity_followup_prompt": f"{book['author']}의 『{book['title']}』의 문학사적 의의와 다양한 해석을 정리해줘.",
        "next_recommendations": [
            {"title": b["title"], "author": b["author"], "reason": recommendation_reason(b), "external": False} for b in recommendations
        ],
        "source_note": "수능 기출 + EBS 연계 한국 고전 일일 리포트"
    }


def rebuild_books_index(output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    daily_dir = output_dir / 'daily'
    books: dict[str, dict] = {}
    try:
        catalog = json.loads(BOOKS_PATH.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        catalog = []
    catalog_by_id = {b.get('id'): b for b in catalog}

    if daily_dir.exists():
        for path in sorted(daily_dir.glob('*.json')):
            try:
                data = json.loads(path.read_text(encoding='utf-8'))
            except (OSError, json.JSONDecodeError) as exc:
                print(f"[WARN] books-index: skip {path.name}: {exc}", flush=True)
                continue
            bid = data.get('book_id')
            if bid is None:
                print(f"[WARN] books-index: {path.name} has no book_id", flush=True)
                continue
            date_str = data.get('date') or path.stem
            key = str(bid)
            entry = books.setdefault(key, {'latest': '', 'dates': []})
            if date_str not in entry['dates']:
                entry['dates'].append(date_str)
            cat = catalog_by_id.get(bid) or {}
            if cat.get('source_rank', 3) >= 4:
                entry['external'] = True
                entry['title_norm'] = _normalize(data.get('title') or cat.get('title', ''))
                entry['author_norm'] = _normalize(data.get('author') or cat.get('author', ''))

    for entry in books.values():
        entry['dates'].sort()
        entry['latest'] = entry['dates'][-1] if entry['dates'] else ''
    sorted_books = {k: books[k] for k in sorted(books.keys(), key=lambda s: int(s))}
    index = {
        'generated_at': datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds'),
        'count': len(sorted_books),
        'books': sorted_books,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'books-index.json').write_text(
        json.dumps(index, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    return index


def save_report(report: dict, update_today: bool = True):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    daily_dir = OUTPUT_DIR / 'daily'
    daily_dir.mkdir(parents=True, exist_ok=True)
    (daily_dir / f"{report['date']}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    if update_today:
        (OUTPUT_DIR / 'today.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    rebuild_books_index(OUTPUT_DIR)


def generate_for_date(target_date: date, update_today: bool = True, force: bool = False):
    target_str = target_date.isoformat()
    daily_path = OUTPUT_DIR / 'daily' / f"{target_str}.json"
    if not force and daily_path.exists():
        report = json.loads(daily_path.read_text(encoding='utf-8'))
        print(f"[INFO] {target_str} already exists — reusing (skip Claude)", flush=True)
        save_report(report, update_today=update_today)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return report

    rotation_books = load_books()
    full_books = load_books(include_external=True)
    book, idx = pick_book(target_date, full_books)
    fallback_recs = next_books(idx, rotation_books, 3)
    excluded_titles = [f"{b['author']} / {b['title']}" for b in full_books]
    prompt = build_prompt(book, target_str, excluded_titles)
    try:
        report = call_claude(prompt)
    except Exception as e:
        print(f"[WARN] Claude API failed: {e}", flush=True)
        report = fallback_report(book, target_str, fallback_recs)
    save_report(report, update_today=update_today)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def date_for_book_id(book_id: int) -> date:
    books = load_books(include_external=True)
    for idx, b in enumerate(books):
        if b.get("id") == book_id:
            start = datetime.strptime(START_DATE, "%Y-%m-%d").date()
            return start + timedelta(days=idx)
    raise ValueError(f"book_id {book_id} not found in books list (READING_MODE={READING_MODE})")


def _parse_arg(arg: str) -> date:
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", arg):
        return datetime.strptime(arg, "%Y-%m-%d").date()
    if re.fullmatch(r"\d+", arg):
        return date_for_book_id(int(arg))
    raise ValueError(f"Argument must be YYYY-MM-DD or a book_id integer, got: {arg!r}")


def generate_for_external(title: str, author: str, update_today: bool = False, force: bool = False) -> dict:
    entry = add_external_book(title, author)
    target_date = date_for_book_id(entry["id"])
    return generate_for_date(target_date, update_today=update_today, force=force)


def main():
    args = [a for a in sys.argv[1:] if a]
    force = "--force" in args

    if "--external" in args:
        i = args.index("--external")
        rest = [a for a in args[i + 1 :] if not a.startswith("--")]
        if len(rest) < 2:
            raise SystemExit('--external requires: --external "<title>" "<author>"')
        title, author = rest[0], rest[1]
        generate_for_external(title, author, update_today=False, force=force)
        return

    positional = [a for a in args if not a.startswith("--")]
    if positional:
        target = _parse_arg(positional[0])
        today = get_today_local()
        generate_for_date(target, update_today=(target == today), force=force)
    else:
        generate_for_date(get_today_local(), force=force)


if __name__ == '__main__':
    main()
