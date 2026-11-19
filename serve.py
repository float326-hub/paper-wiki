#!/usr/bin/env python3
"""논문 위키 로컬 서버 (Claude Code 버전)

표준 라이브러리만 사용한다. 설치할 것이 없다.
    python serve.py            # http://127.0.0.1:8765 에서 열림
    python serve.py --port 9000

데이터는 data/ 폴더의 JSON 파일에 저장된다.
    data/papers/<id>.json      논문 1편 = 파일 1개
    data/insights/<id>.json    인사이트 1개 = 파일 1개
    data/layout/graph.json     연결 지도 점 위치
    data/qa/<id>.json          질문 탭 기록

API (위키 화면이 사용)
    GET    /api/<col>          문서 목록 [{id, data}]
    GET    /api/<col>/<id>     문서 하나 (없으면 404)
    PUT    /api/<col>/<id>     통째로 저장 (set)
    PATCH  /api/<col>/<id>     필드 합치기 (update, 없으면 404)
    DELETE /api/<col>/<id>     삭제
    GET    /api/ask            질문 기능을 쓸 수 있는지 {available}
    POST   /api/ask            {turns:[{role,content}]} -> {text}

질문 기능은 이 PC에 설치된 Claude Code CLI(claude)를 불러 답한다.
API 키를 읽거나 저장하지 않는다. CLI가 없으면 질문 탭만 꺼진다.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
COLLECTIONS = {"papers", "insights", "layout", "qa"}
ID_RE = re.compile(r"^[A-Za-z0-9_\-.~:@+]{1,200}$")
ALLOWED_HOSTS = {"127.0.0.1", "localhost", "[::1]"}
MAX_BODY = 2 * 1024 * 1024          # 요청 본문 최대 2MB
ASK_TIMEOUT = 300                   # 질문 하나에 최대 5분
# 질문 답변은 위키 내용만 보고 쓰게 한다: 파일·명령·웹 도구를 모두 막는다.
ASK_BLOCKED_TOOLS = "Bash,Edit,Write,MultiEdit,NotebookEdit,Read,Glob,Grep,WebFetch,WebSearch,Task"


def claude_cli():
    return shutil.which("claude")


def turns_to_prompt(turns):
    """화면이 보낸 대화(첫 턴=규칙+위키, 이후 질문/답변)를 CLI에 넘길 글 하나로 만든다."""
    parts = []
    for i, t in enumerate(turns):
        role, text = t.get("role"), str(t.get("content", ""))
        if i == 0:
            parts.append(text)
        elif role == "assistant":
            parts.append("### 앞에서 한 답변\n" + text)
        else:
            parts.append("### 연구자\n" + text)
    return "\n\n".join(parts)


def doc_path(col, doc_id):
    if col not in COLLECTIONS or not ID_RE.match(doc_id) or doc_id in (".", ".."):
        return None
    return DATA / col / f"{doc_id}.json"


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def deep_merge(base, patch):
    for k, v in patch.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            deep_merge(base[k], v)
        else:
            base[k] = v
    return base


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def log_message(self, fmt, *args):
        first = args[0] if args else ""
        if not (isinstance(first, str) and "/api/" in first):
            super().log_message(fmt, *args)

    # 화면 파일을 바꾸면 새로고침만으로 바로 반영되게 (브라우저가 옛 파일을 들고 있지 않게)
    def end_headers(self):
        if not (self.path or "").startswith("/api/"):
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    # ---- helpers ----
    def send_json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def parts(self):
        p = self.path.split("?", 1)[0]
        if not p.startswith("/api/"):
            return None
        return [x for x in p[5:].split("/") if x]

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > MAX_BODY:
            raise ValueError("body too large")
        data = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
        if not isinstance(data, dict):
            raise ValueError("body must be a JSON object")
        return data

    # ---- 다른 웹사이트가 이 서버를 건드리지 못하게 ----
    def host_ok(self):
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0].lower()
        return host in ALLOWED_HOSTS

    def json_request(self):
        # JSON 요청만 받으면, 다른 사이트에서 보낸 요청은 브라우저가 미리 막는다(CORS preflight).
        return (self.headers.get("Content-Type") or "").split(";")[0].strip().lower() == "application/json"

    def guard(self, write=False):
        if not self.host_ok():
            self.send_json(403, {"error": "forbidden host"})
            return False
        if write and not self.json_request():
            self.send_json(415, {"error": "JSON only"})
            return False
        return True

    # ---- block serving private folders ----
    def blocked(self):
        p = self.path.split("?", 1)[0].lower()
        return p.startswith(("/pdfs", "/.git", "/.claude", "/data", "/tools")) or p.endswith((".py", ".md", ".env"))

    def do_GET(self):
        if not self.guard():
            return
        parts = self.parts()
        if parts == ["ask"]:
            return self.send_json(200, {"available": bool(claude_cli())})
        if parts is None:
            if self.blocked():
                return self.send_error(404)
            return super().do_GET()
        if len(parts) == 1 and parts[0] in COLLECTIONS:
            folder = DATA / parts[0]
            out = []
            if folder.exists():
                for f in sorted(folder.glob("*.json")):
                    try:
                        out.append({"id": f.stem, "data": read_json(f)})
                    except Exception as e:  # 깨진 파일은 건너뛰고 알려 준다
                        print(f"[경고] {f.name} 을(를) 읽지 못했어요: {e}", file=sys.stderr)
            return self.send_json(200, out)
        if len(parts) == 2:
            path = doc_path(*parts)
            if not path:
                return self.send_json(400, {"error": "bad path"})
            if not path.exists():
                return self.send_json(404, {"error": "not found"})
            return self.send_json(200, {"id": parts[1], "data": read_json(path)})
        return self.send_json(400, {"error": "bad path"})

    def _write(self, mode):
        if not self.guard(write=mode != "delete"):
            return
        parts = self.parts()
        if not parts or len(parts) != 2:
            return self.send_json(400, {"error": "bad path"})
        path = doc_path(*parts)
        if not path:
            return self.send_json(400, {"error": "bad path"})
        try:
            data = self.body() if mode != "delete" else None
        except Exception as e:
            return self.send_json(400, {"error": str(e)})
        if mode == "set":
            write_json(path, data)
        elif mode == "update":
            if not path.exists():
                return self.send_json(404, {"error": "not found"})
            write_json(path, deep_merge(read_json(path), data))
        else:
            if path.exists():
                path.unlink()
        return self.send_json(200, {"ok": True})

    def do_POST(self):
        if not self.guard(write=True):
            return
        if self.parts() != ["ask"]:
            return self.send_json(404, {"error": "not found"})
        cli = claude_cli()
        if not cli:
            return self.send_json(503, {"code": "upstream_error", "error": "Claude Code 명령(claude)을 찾지 못했어요."})
        try:
            turns = self.body().get("turns")
            if not isinstance(turns, list) or not turns:
                raise ValueError("turns가 비어 있어요")
            prompt = turns_to_prompt(turns)
        except Exception as e:
            return self.send_json(400, {"code": "invalid_request", "error": str(e)})
        try:
            # 빈 임시 폴더에서 실행해, 혹시 도구가 열려도 위키 파일 밖의 것을 보지 않게 한다.
            with tempfile.TemporaryDirectory() as tmp:
                r = subprocess.run(
                    [cli, "-p", "--output-format", "text", "--disallowedTools", ASK_BLOCKED_TOOLS],
                    input=prompt, capture_output=True, text=True, encoding="utf-8",
                    timeout=ASK_TIMEOUT, cwd=tmp,
                )
        except subprocess.TimeoutExpired:
            return self.send_json(504, {"code": "upstream_error", "error": "답이 너무 오래 걸려서 멈췄어요. 질문을 좁혀 보세요."})
        except Exception as e:
            return self.send_json(500, {"code": "upstream_error", "error": f"Claude Code를 실행하지 못했어요: {e}"})
        text = (r.stdout or "").strip()
        if r.returncode != 0 or not text:
            msg = (r.stderr or "").strip().splitlines()
            return self.send_json(502, {"code": "upstream_error", "error": "Claude Code가 답하지 못했어요." + (f" ({msg[-1][:200]})" if msg else "")})
        return self.send_json(200, {"text": text})

    def do_PUT(self):
        self._write("set")

    def do_PATCH(self):
        self._write("update")

    def do_DELETE(self):
        self._write("delete")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()
    for c in COLLECTIONS:
        (DATA / c).mkdir(parents=True, exist_ok=True)
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"Paper Wiki: {url}  (끄려면 Ctrl+C)")
    if not args.no_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
