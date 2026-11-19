#!/usr/bin/env python3
"""data/ 를 점검한다: JSON 문법, 필수 필드, 관리 번호 중복, 깨진 연결, 한쪽만 있는 연결.

    python tools/check_data.py
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQ = ["no", "pubType", "title", "authors", "journal", "pubDate", "fields", "keywords", "status",
       "rating", "problem", "method", "result", "limitations", "interesting", "questions", "memo",
       "related", "relatedWhy", "link", "doi", "volume", "issue", "pages", "addedAt", "readAt"]
PUBTYPES = {"article", "conference", "workshop", "preprint", "chapter", "other"}
STATUS = {"plan", "read", "done", "cancel"}
ACCESS = {"", "gold", "hybrid", "bronze", "free", "green", "closed"}

def main():
    problems, papers = [], {}
    for f in sorted((ROOT / "data" / "papers").glob("*.json")):
        try:
            papers[f.stem] = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            problems.append(f"{f.name}: JSON 오류 {e}")
    nos = {}
    for pid, p in papers.items():
        miss = [k for k in REQ if k not in p]
        if miss: problems.append(f"{pid}: 빠진 필드 {miss}")
        if p.get("pubType") not in PUBTYPES: problems.append(f"{pid}: pubType '{p.get('pubType')}'")
        if p.get("status") not in STATUS: problems.append(f"{pid}: status '{p.get('status')}'")
        if p.get("access", "") not in ACCESS: problems.append(f"{pid}: access '{p.get('access')}'")
        oa = p.get("oaUrl", "")
        if oa and not str(oa).startswith(("http://", "https://")): problems.append(f"{pid}: oaUrl이 링크가 아님")
        no = p.get("no")
        if isinstance(no, int) and no > 0:
            if no in nos: problems.append(f"관리 번호 #{no:02d} 중복: {nos[no]}, {pid}")
            nos[no] = pid
        else:
            problems.append(f"{pid}: 관리 번호 없음")
        for r in p.get("related", []):
            if r not in papers: problems.append(f"{pid}: 없는 논문 '{r}'에 연결됨")
            elif pid not in papers[r].get("related", []): problems.append(f"{pid} → {r}: 한쪽만 연결됨")
        for k in (p.get("relatedWhy") or {}):
            if k not in p.get("related", []): problems.append(f"{pid}: relatedWhy에 연결 안 된 '{k}'")
    print(f"논문 {len(papers)}편 점검, 문제 {len(problems)}개")
    for x in problems: print(" -", x)
    sys.exit(1 if problems else 0)

if __name__ == "__main__":
    main()
