#!/usr/bin/env python3
"""claude.ai 위키에서 받은 JSON 백업(paper-wiki-backup_*.json)을 data/ 파일로 풀어 넣는다.

    python tools/import_backup.py paper-wiki-backup_2026-11-18.json
    python tools/import_backup.py backup.json --overwrite   # 같은 id가 있으면 덮어쓰기
"""
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ID_RE = re.compile(r"^[A-Za-z0-9_\-.~:@+]{1,200}$")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("backup")
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args()
    j = json.load(open(a.backup, encoding="utf-8"))
    if isinstance(j, list):
        j = {"papers": j}
    n = {"papers": 0, "insights": 0, "skip": 0}
    for col in ("papers", "insights"):
        folder = ROOT / "data" / col
        folder.mkdir(parents=True, exist_ok=True)
        for item in j.get(col, []) or []:
            item = dict(item)
            doc_id = item.pop("id", None)
            if not doc_id or not ID_RE.match(doc_id):
                print(f"[건너뜀] id가 없거나 올바르지 않아요: {item.get('title','')[:40]}", file=sys.stderr)
                n["skip"] += 1
                continue
            path = folder / f"{doc_id}.json"
            if path.exists() and not a.overwrite:
                n["skip"] += 1
                continue
            path.write_text(json.dumps(item, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            n[col] += 1
    print(f"논문 {n['papers']}편, 인사이트 {n['insights']}개를 넣었어요. 건너뜀 {n['skip']}개.")

if __name__ == "__main__":
    main()
