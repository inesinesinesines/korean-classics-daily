"""One-shot script: create the Korean Classics Daily Notion DB under the
existing dashboard page. Run once, then discard.
"""
import json
import os
import sys
from notion_client import Client

NOTION_API_KEY = os.environ["NOTION_API_KEY"]
PARENT_PAGE_ID = os.environ["PARENT_PAGE_ID"]

SUBGENRES = [
    "전기소설", "몽자류소설", "판소리계소설", "영웅·군담소설", "가정소설",
    "한문단편", "우화소설", "애정소설", "풍자소설", "역사·군담소설",
    "역사소설", "애정·영웅소설", "몽유록·애정소설", "역사·가정소설",
    "판소리계소설·우화소설", "판소리계소설·풍자소설", "한문단편·애정소설",
    "향가(4구체)", "향가(8구체)", "향가(10구체)", "고려가요", "백제가요",
    "평시조", "연시조", "사설시조", "연시조(교훈)",
    "한시(5언절구)", "한시(7언절구)", "한시(7언고시)", "영웅서사한시",
    "양반가사·강호가사", "기행가사", "연군가사", "은일가사", "전쟁가사",
    "내방가사·규방가사", "월령체가사", "유배가사", "내방가사·풍자가사",
    "설(說)", "기(記)·기행문", "제문", "내간체수필·우화", "궁정수필·회고록",
    "미상",
]
PERIODS = [
    "백제", "신라", "통일신라", "고려", "고려말·조선초",
    "조선전기", "조선중기", "조선후기", "미상",
]
CATEGORIES = ["고전소설", "고전시가", "가사", "고전수필", "고전문학"]
READING_MODES = ["ranked", "strict", "extended", "preview"]


def opt(name):
    return {"name": name}


def main():
    notion = Client(auth=NOTION_API_KEY)
    payload = {
        "parent": {"type": "page_id", "page_id": PARENT_PAGE_ID},
        "title": [{"type": "text", "text": {"content": "Korean Classics Daily"}}],
        "properties": {
            "Name": {"title": {}},
            "Date": {"date": {}},
            "Book ID": {"number": {"format": "number"}},
            "Author": {"rich_text": {}},
            "Title": {"rich_text": {}},
            "Category": {"select": {"options": [opt(x) for x in CATEGORIES]}},
            "Subgenre": {"select": {"options": [opt(x) for x in SUBGENRES]}},
            "Period": {"select": {"options": [opt(x) for x in PERIODS]}},
            "Source Rank": {"number": {"format": "number"}},
            "Source Basis": {"rich_text": {}},
            "Reading Mode": {"select": {"options": [opt(x) for x in READING_MODES]}},
            "One-line Summary": {"rich_text": {}},
            "Full Summary": {"rich_text": {}},
            "Literary Significance": {"rich_text": {}},
            "Interpretations": {"rich_text": {}},
            "Keywords": {"multi_select": {"options": []}},
            "Discussion Question": {"rich_text": {}},
            "JSON URL": {"url": {}},
            "Web App URL": {"url": {}},
        },
    }
    db = notion.databases.create(**payload)
    print(json.dumps({
        "id": db["id"],
        "url": db.get("url", ""),
        "title": db.get("title", [{}])[0].get("plain_text", ""),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.exit(main())
