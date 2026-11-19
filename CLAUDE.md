# 논문 위키 (Claude Code 버전): AI 작업 지침

이 저장소는 사용자가 읽었거나 읽을 논문을 정리하는 개인 위키다. 데이터는 `data/`의 JSON 파일이고, `index.html`은 `serve.py`가 띄우는 로컬 화면이다. **사용자에게는 항상 한국어로 답한다.**

## 구조
```
index.html            위키 화면 (홈 통계·연결 지도·카드/표/칸반·질문·인사이트 보드·참고문헌·백업)
serve.py              로컬 서버 + 파일 API + 질문 API (표준 라이브러리만, python serve.py)
config.json           화면 제목과 분야 문구
data/papers/<id>.json     논문 1편 = 파일 1개
data/insights/<id>.json   인사이트 1개 = 파일 1개 (사용자 전용)
data/layout/graph.json    연결 지도 점 위치 (화면이 관리, 건드리지 않음)
data/qa/<id>.json         질문 탭 기록 (화면이 관리, 건드리지 않음)
pdfs/                 사용자가 저장한 논문 PDF. 파일명은 관리 번호로 시작 (예: 07_example2024.pdf)
tools/check_data.py   데이터 점검 (필드·번호 중복·한쪽 연결·무료/유료 값)
tools/import_backup.py  claude.ai 판 위키의 JSON 백업을 data/로 풀기
.claude/skills/paper-wiki-add/SKILL.md  논문 넣기 절차
```
- 화면은 2.5초마다 파일을 다시 읽으므로, 파일을 고치면 열려 있는 위키에 곧 반영된다.
- 파일을 쓸 때는 UTF-8, 들여쓰기 2칸, `ensure_ascii=False` 형태의 JSON으로 쓴다.

## 0. 비밀·개인 정보
- API 키, 토큰, 비밀번호, 개인 연락처를 저장소의 어떤 파일에도 쓰지 않는다. 질문 기능은 Claude Code CLI를 쓰므로 키가 필요 없다.
- `data/`와 `pdfs/`는 `.gitignore`로 빠져 있다. 사용자가 요청하지 않으면 이 설정을 바꾸지 않고, git commit·push도 하지 않는다.

## 1. 보안: 미출판 논문 (최우선)
사용자가 PDF(`pdfs/`의 파일 포함)를 주면 아직 공개되지 않은 원고일 수 있다.
1. 정리하기 전에 공개 여부부터 확인한다. PDF 안의 DOI·arXiv 번호·저널 정보를 먼저 보고, 웹 검색이 필요하면 **제목만** 검색어로 쓴다. 초록·본문 문장·수치·고유한 방법 이름은 검색어에 넣지 않는다.
2. 공개 버전을 못 찾으면 검색을 멈추고, 넣기 전에 묻는다: "공개된 버전을 찾지 못했어요. 미출판 원고일 수 있는데 위키에 넣을까요?"
3. 넣으라고 하면 memo에 "미출판 원고 (공개 버전 미확인, 추가일 기준)"라고 적고 link·doi·access는 비운다.
4. 미출판 논문의 내용은 웹 검색, 외부 서비스, 커밋 메시지, 공개 저장소 어디에도 내보내지 않는다.
5. 사용자가 "미출판이야" 또는 "검색하지 마"라고 하면 검색 없이 미출판으로 처리한다.

## 2. 누가 무엇을 적는가
- **Claude가 적는 것**: 서지 정보, 출판 유형, 분야 태그, 키워드(영어 원어 3~6개), 문제·방법·결과(각 2~4문장, 핵심 수치 포함), 한계점, 무료/유료, 관련 논문 연결과 이유.
  - 한계점은 **논문이 스스로 밝힌 것만** 적는다. Claude의 평가("아쉬운 점")는 적지 않는다.
  - 확인되지 않은 정보는 지어내지 않고 비운다.
  - 키워드는 기존 논문에 이미 있는 표기를 먼저 쓴다 (예: 이미 "Graph neural network"가 있으면 새로 "graph neural networks"를 만들지 않는다). 같은 키워드를 함께 쓴 논문끼리 연결 지도에서 묶여 보인다.
- **Claude가 적지 않는 것**: `interesting`(흥미로운 점), `questions`(궁금한 점)은 항상 `""`. 인사이트 보드는 사용자가 "인사이트에 추가해줘"라고 할 때만, 준 내용을 지어내지 않고 정리해서 넣는다.
- **memo**: 특별한 경우에만 한 줄 (출처, 리뷰 논문, 원문을 못 열어 일부를 비움, 권·호 미배정 등).
- 사용자가 직접 적은 interesting·questions·memo·인사이트·연결은 요청 없이 고치지 않는다.
- 링크와 사용자가 적은 제목이 서로 다른 문헌이면 넣기 전에 묻는다.

## 3. 관련 논문 연결 기준
기존 논문 전체와 비교해, 아래 중 하나에 **분명히** 해당할 때만 연결한다.
- **유사 소재**: 같은 물질·물질군
- **유사 방법**: 핵심 알고리즘·공정·워크플로가 같음
- **상호 보완**: 한쪽의 결과·도구가 다른 쪽 문제를 채우거나, 같은 주제를 다른 측면에서 다룸
- **후속 연구**: 직접 발전시키거나 이어감
- **비교 대상**: 기준 모델·비교 대상으로 직접 씀

같은 연구실·저자라는 이유만, 분야 태그만 겹치는 경우, 억지로 이유를 만들어야 하는 경우는 연결하지 않는다. 연결하면 **양쪽 파일 모두** `related`에 상대 id를 넣고 `relatedWhy`에 `"유형: 한두 문장"`을 적는다. 관계성 지수(연결 수)와 허브 표시는 화면이 자동 계산한다.

## 4. 논문 파일 스키마 (`data/papers/<id>.json`, 모든 필드 필수)
| 필드 | 타입 | 내용 |
| --- | --- | --- |
| no | number | 관리 번호. `pdfs/`의 PDF 번호와 맞춘다. 새 논문은 최대값+1, 중복 금지, 삭제해도 당기지 않음 |
| pubType | string | article / conference / workshop / preprint / chapter / other |
| title | string | 제목 |
| authors | string[] | "성, 이름" (예: "Vaswani, Ashish"). 한국어는 "홍길동" 또는 "홍, 길동" |
| journal | string | 저널, 학회·워크숍, 서버("arXiv"), 책 챕터면 책 제목 |
| publisher | string | 출판사 (주로 책 챕터) |
| pubDate | string | YYYY-MM-DD / YYYY-MM / YYYY |
| fields | string[] | 분야 태그 (기존 태그 우선 사용) |
| keywords | string[] | 영어 원어 |
| status | string | plan(읽을 예정) / read(읽는 중) / done(다 읽음) / cancel(취소) |
| rating | number | 0~5, 사용자가 정함 (Claude는 0) |
| problem, method, result, limitations | string | 위 규칙대로 |
| interesting, questions | string | "" |
| memo | string | 특별한 경우만 |
| related | string[] | 연결된 논문 id |
| relatedWhy | object | `{ "<상대 id>": "유형: 이유" }` |
| link, doi | string | doi는 `https://doi.org/` 없이 |
| access | string | 무료/유료: gold / hybrid / bronze / free / green / closed / "" (미확인) |
| oaUrl | string | 무료로 읽을 수 있는 본문 링크 (`https://`). 유료·미확인이면 "" |
| oaCheckedAt | string | 무료/유료를 확인한 날 YYYY-MM-DD |
| volume, issue, pages | string | 서지 정보 |
| addedAt, readAt | string | YYYY-MM-DD (status가 done이면 readAt 채움) |

id(=파일명)는 `성연도-핵심어` 형식, 영문 소문자·숫자·하이픈만 (예: `vaswani2017-attention`).

화면 표시: gold·hybrid·bronze·free → 무료, green → 무료 사본(프리프린트·기관 저장소), closed → 유료.

### 무료/유료 확인 방법
1. DOI가 있으면 OpenAlex를 조회한다. **DOI만** 보내고 개인 정보(이메일 등)는 넣지 않는다.
   `https://api.openalex.org/works/doi:<DOI>?select=doi,title,open_access,best_oa_location`
   - `open_access.oa_status`를 그대로 `access`에 쓴다 (`diamond`는 `gold`로).
   - `oaUrl`: `best_oa_location.pdf_url`이 PDF면 그것, 아니면 `open_access.oa_url`. 이미지(.jpg 등)를 가리키면 `https://doi.org/<DOI>`.
2. DOI가 없으면: arXiv 등 프리프린트는 `green`(oaUrl = arXiv 주소), OpenReview처럼 출판처가 무료 공개하면 `free`, 판단할 수 없으면 `""`.
3. 미출판 원고는 조회하지 않는다.

## 5. 인사이트 파일 스키마 (`data/insights/<id>.json`, 사용자 전용)
title, body, type(idea / question / direction / counter), status(thinking / reviewed / discuss / doing / hold), papers(관련 논문 id), links(**출발점** 인사이트 id: 이 생각이 비롯된 인사이트), createdAt·updatedAt(ISO 시각). x, y는 넣지 않는다(화면이 배치).

## 6. 위키에 질문하기
사용자가 "위키에 질문: …", "위키에서 찾아줘", "내 논문들 중에…"처럼 물으면, 화면의 질문 탭과 같은 규칙으로 답한다.
1. `data/papers/*.json`만 근거로 쓴다. 웹 검색, 일반 지식으로 빈칸을 메우지 않는다.
2. 근거 논문을 문장 끝에 `[#05]`처럼 관리 번호로 표시한다. 위키에 없는 번호는 쓰지 않는다.
3. 위키만으로 답할 수 없으면 "위키에 이 주제를 다룬 논문이 없어요"라고 말하고, 어떤 논문을 추가하면 좋을지 한 줄로 제안한다.
4. 정리는 원문이 아니라 요약이다. 요약에 없는 세부는 "위키 정리에는 없음"이라고 하고, `pdfs/`의 원문을 확인하라고 한다(사용자가 원하면 그 PDF를 읽어서 답한다).
5. 논문에 적힌 내용과 Claude의 추론을 구분하고, 추론에는 "(추론)"을 붙인다.
6. `interesting`·`questions`·인사이트는 사용자 본인의 생각이다. 논문의 주장처럼 인용하지 않는다.

## 7. 작업 후 확인과 보고
- 파일을 바꾼 뒤 `python tools/check_data.py`로 점검하고, 문제가 있으면 고친다.
- 보고는 짧게: `#번호 제목 (저자, 저널, 연도)`, 상태, 분야 태그, 무료/유료, 연결한 논문과 유형(분야만 겹쳐서 연결 안 한 논문이 있으면 한 줄), 비워 둔 칸과 이유. 정리한 본문 전체를 채팅에 늘어놓지 않는다.

## 8. 화면 코드를 고칠 때
- `index.html` 하나에 CSS·JS가 모두 있다. 위쪽 `<script>`의 로컬 저장소 연결부(`window.claude` 정의)는 serve.py API와 짝이므로 함께 고친다.
- 화면에서 저장할 때 `sanitize()`에 없는 필드는 지워진다. 논문 필드를 새로 만들면 `sanitize()`, CSV 열, 이 문서 4장, `tools/check_data.py`를 함께 고친다.
- 다크 모드와 절제된 디자인을 유지한다(그라데이션·장식 과다 금지). 폰 화면에서도 깨지지 않게 한다.
- 연결 지도 배치는 "배치 새로고침" 버튼을 누를 때만 다시 계산한다. 이 동작을 유지한다.
