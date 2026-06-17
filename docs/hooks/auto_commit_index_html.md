# auto_commit_index_html Stop Hook

## 목적
Codex 작업이 끝날 때 `index.html`만 자동으로 커밋하는 Stop hook 설계입니다.
`index.html`이 바뀌었을 때만 동작하고, 바뀌지 않았으면 아무 것도 커밋하지 않습니다.

## 파일 구조
- `.codex/rules/default.rules`: Stop hook wrapper만 실행 가능하도록 허용합니다.
- `.codex/hooks.json`: Codex Stop 이벤트를 등록합니다.
- `tools/hooks/auto_commit_index_html.py`: 실제 자동 커밋 로직을 수행합니다.
- `.codex/logs/auto_commit_index_html.log`: wrapper 실행 시 자동 생성되는 실행 로그입니다.

## Rules 역할
Rules는 Stop hook에서 쓰는 wrapper 명령만 허용합니다.
- Windows: `py tools/hooks/auto_commit_index_html.py`
- macOS/Linux: `python3 tools/hooks/auto_commit_index_html.py`

아래 명령은 허용하지 않습니다.
- `git commit`
- `git add .`
- `git add -A`
- `py` 단독 실행

## Stop hook 역할
Stop 이벤트가 발생하면 wrapper를 실행합니다.
이 저장소에서는 Windows와 macOS/Linux 명령을 각각 위의 고정 명령으로 등록합니다.

## Wrapper 동작
1. `git rev-parse --show-toplevel`로 repo root를 찾습니다.
2. `.codex/logs/auto_commit_index_html.log`를 append 모드로 준비합니다.
3. 실행 시각, repo root, Python 실행 파일, OS 정보를 기록합니다.
4. Python, Git, Git repo, `index.html`, `git user.name`, `git user.email`, `.git/index.lock` 상태를 확인합니다.
5. `git status --porcelain -- index.html`로 `index.html` 변경 여부만 확인합니다.
6. 변경이 없으면 `NO_INDEX_HTML_CHANGE`를 기록하고 종료합니다.
7. 변경이 있으면 `INDEX_HTML_CHANGED`를 기록합니다.
8. `git add -- index.html`만 실행합니다.
9. `pre-commit`이 있으면 `sys.executable -m pre_commit run --files index.html`를 실행합니다.
10. `pre-commit`이 없으면 `PRE_COMMIT_NOT_INSTALLED_SKIP`를 기록하고 계속 진행합니다.
11. `pre-commit`이 실패하면 `PRE_COMMIT_FAILED`를 기록하고 커밋하지 않습니다.
12. `git add -- index.html`만 다시 실행합니다.
13. `git diff --cached --quiet -- index.html`로 staged 상태를 확인합니다.
14. staged 변경이 없으면 `NO_STAGED_INDEX_HTML_CHANGE`를 기록하고 종료합니다.
15. staged 변경이 있으면 `git commit -m "auto: update index.html"`를 실행합니다.
16. 성공하면 `COMMIT_SUCCESS`와 commit hash를 기록합니다.
17. 실패하면 `GIT_COMMIT_FAILED`와 에러 메시지를 기록합니다.

## 로그 위치
- 로그 경로: `.codex/logs/auto_commit_index_html.log`
- 로그 디렉터리가 없으면 wrapper가 자동으로 만듭니다.
- 모든 종료 경로를 로그에 남깁니다.
- 로그 파일은 자동 커밋 대상에 포함하지 않습니다. 자동 커밋 대상은 `index.html`뿐입니다.

## Trust 필요 여부
네. 실제 Stop hook이 실행되려면 사용자가 `/hooks`를 통해 hook을 켜거나, rules trust를 허용해야 합니다.

## 테스트 방법
이번 턴에서는 테스트를 실행하지 않았습니다.
나중에 확인할 때는 `index.html`을 바꾼 뒤 Stop hook을 실행하고, 로그와 커밋 결과를 보면 됩니다.
