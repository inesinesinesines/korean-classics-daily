"""Merge exam-frequency research into books.json and re-sort by importance.

Usage:
  python scripts/merge_exam_data.py research1.json research2.json ...

Each research file is a JSON array of objects with fields:
  title, exam_count_sat, exam_count_mock, ebs_count, latest_year,
  exam_history, importance, notes

Match is performed on normalized title. After merge, entries are sorted by:
  importance DESC, exam_count_sat DESC, source_rank ASC, title ASC
Then ids are reassigned 1..N in the new order.
"""
import json
import sys
from pathlib import Path

BOOKS_PATH = Path(__file__).parent.parent / "books.json"


def norm(s: str) -> str:
    return (s or "").strip().replace("『", "").replace("』", "").replace("「", "").replace("」", "")


def load_research(paths):
    out = {}  # normalized title -> research dict
    for p in paths:
        data = json.loads(Path(p).read_text(encoding="utf-8"))
        for row in data:
            key = norm(row.get("title", ""))
            if not key:
                continue
            out[key] = row
    return out


def merge_one(book: dict, research: dict, research_lookup: dict) -> dict:
    key = norm(book["title"])
    row = research_lookup.get(key)
    if row is None:
        # Try partial matches
        for rk, rv in research_lookup.items():
            if key in rk or rk in key:
                row = rv
                print(f"[partial match] {book['title']} -> {rv.get('title')}")
                break
    if row is None:
        print(f"[UNMATCHED] {book['title']}")
        return book
    book["importance"] = row.get("importance") or book.get("importance") or derive_importance(book)
    book["exam_count_sat"] = row.get("exam_count_sat") or 0
    book["exam_count_mock"] = row.get("exam_count_mock") or 0
    book["ebs_count"] = row.get("ebs_count") or 0
    book["latest_year"] = row.get("latest_year") or ""
    if row.get("exam_history"):
        book["exam_history"] = row["exam_history"]
    if row.get("notes"):
        book["research_notes"] = row["notes"]
    return book


def derive_importance(book: dict) -> int:
    """Fallback: map source_rank to importance if research didn't provide one."""
    return {1: 4, 2: 3, 3: 2, 4: 1}.get(book.get("source_rank", 3), 3)


def sort_key(b: dict):
    return (
        -(b.get("importance") or 0),
        -(b.get("exam_count_sat") or 0),
        -(b.get("exam_count_mock") or 0),
        -(b.get("ebs_count") or 0),
        b.get("source_rank", 3),
        b["title"],
    )


def main():
    if len(sys.argv) < 2:
        print("Usage: merge_exam_data.py research1.json [research2.json ...]")
        sys.exit(2)
    research = load_research(sys.argv[1:])
    print(f"Loaded {len(research)} research entries")

    books = json.loads(BOOKS_PATH.read_text(encoding="utf-8"))
    for b in books:
        merge_one(b, {}, research)
        if "importance" not in b or b["importance"] is None:
            b["importance"] = derive_importance(b)

    books.sort(key=sort_key)
    for new_id, b in enumerate(books, 1):
        b["id"] = new_id

    BOOKS_PATH.write_text(
        json.dumps(books, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(books)} entries. Top 10 by importance:")
    for b in books[:10]:
        print(f"  #{b['id']:2d} imp={b['importance']} sat={b.get('exam_count_sat',0)} mock={b.get('exam_count_mock',0)} ebs={b.get('ebs_count',0)} - {b['author']} / {b['title']}")


if __name__ == "__main__":
    main()
