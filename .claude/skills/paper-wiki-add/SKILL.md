---
name: paper-wiki-add
description: 논문 링크·DOI·PDF·제목을 받아 이 저장소의 논문 위키(data/papers/*.json)에 정리해 넣을 때 사용. "읽을 논문", "읽는 중", "위키에 추가" 같은 요청이나 논문 링크·DOI만 보낸 경우, pdfs/의 새 PDF를 정리해 달라는 경우.
---

# 논문 위키에 논문 넣기

규칙의 원본은 저장소 루트의 `CLAUDE.md`다. 이 스킬은 그 규칙을 따르는 절차만 정리한다.

1. **PDF면 보안부터.** CLAUDE.md 1장대로 공개 여부를 확인한다. 웹 검색은 제목만 쓴다. 공개 버전을 못 찾으면 넣기 전에 묻는다.
2. **서지 정보 확인.** 링크·DOI를 WebFetch로 열고, 막히면 WebSearch로 PubMed·PMC·ResearchGate·보도자료 같은 공개 출처를 찾는다. 출처가 우회 경로면 memo에 한 줄 남긴다. 링크와 사용자가 적은 제목이 다른 문헌이면 묻는다.
3. **기존 데이터 읽기.** `data/papers/*.json`을 모두 읽어 중복 여부(DOI·제목), 최대 `no`, 연결 후보를 확인한다.
4. **번호·유형·id 정하기.**
   - `no` = 최대값 + 1 (사용자가 번호를 말하면 그 값, 중복이면 알림). `pdfs/`에 같은 번호로 시작하는 PDF가 있으면 그 파일이 이 논문인지 확인한다.
   - `pubType`: article / conference / workshop / preprint(arXiv 등) / chapter(journal=책 제목, publisher=출판사) / other.
   - id = `성연도-핵심어` (영문 소문자·숫자·하이픈).
5. **무료/유료 확인.** CLAUDE.md 4장의 방법(OpenAlex, DOI만 보냄)으로 `access`, `oaUrl`, `oaCheckedAt`을 채운다. 미출판 원고는 조회하지 않는다.
6. **파일 쓰기.** `data/papers/<id>.json`에 CLAUDE.md 4장의 모든 필드를 넣는다. interesting·questions는 `""`, rating은 0. 상태를 말하지 않으면 `plan`, addedAt은 오늘.
7. **연결.** CLAUDE.md 3장 기준에 분명히 맞는 기존 논문만 고른다. 새 파일과 상대 파일 **양쪽** 모두에 `related`, `relatedWhy`를 추가한다. 상대 파일의 다른 필드는 건드리지 않는다.
8. **점검.** `python tools/check_data.py`를 실행해 문제가 없게 한다.
9. **짧게 보고.** 번호·제목(저자, 저널, 연도)·상태·분야 태그·무료/유료, 연결한 논문과 유형, 분야만 겹쳐서 연결 안 한 논문, 비워 둔 칸과 이유. 번호가 PC의 PDF 번호와 다르면 알려 달라고 한 줄.

여러 편을 한꺼번에 받으면 3번을 한 번만 하고, 번호를 차례로 붙여 같은 절차를 반복한다.
