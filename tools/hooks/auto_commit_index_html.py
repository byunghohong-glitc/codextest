from __future__ import annotations

import datetime as dt
import importlib.util
from pathlib import Path
import platform
import shutil
import subprocess
import sys


LOG_NAME = "auto_commit_index_html.log"
TARGET_FILE = "index.html"
COMMIT_MESSAGE = "auto: update index.html"


def run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        text=True,
        capture_output=True,
    )


def append_log(log_path: Path, message: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    with log_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(f"{timestamp} {message}\n")


def emit(status: str, log_path: Path, extra: str | None = None) -> None:
    line = status if extra is None else f"{status} {extra}"
    print(line)
    append_log(log_path, line)


def finish(status: str, log_path: Path, extra: str | None = None) -> int:
    emit(status, log_path, extra)
    return 0


def resolve_repo_root(start_dir: Path) -> Path | None:
    try:
        git_cp = run_git(["rev-parse", "--show-toplevel"], cwd=start_dir)
    except OSError:
        return None
    if git_cp.returncode != 0:
        return None
    value = git_cp.stdout.strip()
    return Path(value) if value else None


def to_abs_path(repo_root: Path, maybe_path: str) -> Path:
    path = Path(maybe_path)
    if path.is_absolute():
        return path
    return repo_root / path


def main() -> int:
    start_dir = Path.cwd()
    log_probe = start_dir / ".codex" / "logs" / LOG_NAME
    git_available = shutil.which("git") is not None

    if not git_available:
        append_log(log_probe, "START")
        emit("GIT_EXECUTABLE_MISSING", log_probe)
        return 0

    repo_root = resolve_repo_root(start_dir)
    if repo_root is None:
        append_log(log_probe, "START")
        emit("GIT_REPO_ROOT_LOOKUP_FAILED", log_probe)
        return 0

    log_path = repo_root / ".codex" / "logs" / LOG_NAME
    append_log(log_path, "START")

    git_exe = shutil.which("git") or "UNKNOWN"
    python_exe = sys.executable or "UNKNOWN"
    os_name = platform.system() or "UNKNOWN"
    os_release = platform.release() or "UNKNOWN"
    emit(
        "ENV_CHECK_OK",
        log_path,
        f"repo_root={repo_root} python={python_exe} git={git_exe} os={os_name} release={os_release}",
    )

    git_version_cp = run_git(["--version"], cwd=repo_root)
    if git_version_cp.returncode == 0:
        append_log(log_path, f"GIT_VERSION={git_version_cp.stdout.strip() or 'UNKNOWN'}")
    else:
        append_log(log_path, f"GIT_VERSION=UNKNOWN {git_version_cp.stderr.strip() or 'UNKNOWN'}")

    is_git_repo_cp = run_git(["rev-parse", "--is-inside-work-tree"], cwd=repo_root)
    is_git_repo = is_git_repo_cp.returncode == 0 and is_git_repo_cp.stdout.strip().lower() == "true"
    append_log(log_path, f"GIT_REPO={is_git_repo}")

    git_dir_cp = run_git(["rev-parse", "--git-dir"], cwd=repo_root)
    if git_dir_cp.returncode == 0 and git_dir_cp.stdout.strip():
        git_dir_raw = Path(git_dir_cp.stdout.strip())
        git_dir = to_abs_path(repo_root, str(git_dir_raw))
    else:
        git_dir = repo_root / ".git"

    index_html = repo_root / TARGET_FILE
    append_log(log_path, f"INDEX_HTML_EXISTS={index_html.exists()}")

    user_name_cp = run_git(["config", "--get", "user.name"], cwd=repo_root)
    user_email_cp = run_git(["config", "--get", "user.email"], cwd=repo_root)
    append_log(log_path, f"GIT_USER_NAME={user_name_cp.stdout.strip() or 'UNKNOWN'}")
    append_log(log_path, f"GIT_USER_EMAIL={user_email_cp.stdout.strip() or 'UNKNOWN'}")

    index_lock = git_dir / "index.lock"
    append_log(log_path, f"GIT_INDEX_LOCK_EXISTS={index_lock.exists()}")

    if not is_git_repo:
        return finish("NOT_GIT_REPO", log_path)

    if not index_html.exists():
        return finish("INDEX_HTML_MISSING", log_path)

    if index_lock.exists():
        return finish("GIT_INDEX_LOCK_PRESENT", log_path)

    status_cp = run_git(["status", "--porcelain", "--", TARGET_FILE], cwd=repo_root)
    if status_cp.returncode != 0:
        return finish("GIT_STATUS_FAILED", log_path, status_cp.stderr.strip() or "UNKNOWN")

    if not status_cp.stdout.strip():
        return finish("NO_INDEX_HTML_CHANGE", log_path)

    emit("INDEX_HTML_CHANGED", log_path)

    add_cp = run_git(["add", "--", TARGET_FILE], cwd=repo_root)
    if add_cp.returncode != 0:
        return finish("GIT_ADD_FAILED", log_path, add_cp.stderr.strip() or "UNKNOWN")

    pre_commit_available = importlib.util.find_spec("pre_commit") is not None
    if pre_commit_available:
        pre_commit_cp = subprocess.run(
            [sys.executable, "-m", "pre_commit", "run", "--files", TARGET_FILE],
            cwd=str(repo_root),
            text=True,
            capture_output=True,
        )
        if pre_commit_cp.returncode != 0:
            return finish(
                "PRE_COMMIT_FAILED",
                log_path,
                pre_commit_cp.stderr.strip() or pre_commit_cp.stdout.strip() or "UNKNOWN",
            )
    else:
        emit("PRE_COMMIT_NOT_INSTALLED_SKIP", log_path)

    add_again_cp = run_git(["add", "--", TARGET_FILE], cwd=repo_root)
    if add_again_cp.returncode != 0:
        return finish("GIT_ADD_FAILED", log_path, add_again_cp.stderr.strip() or "UNKNOWN")

    staged_cp = run_git(["diff", "--cached", "--quiet", "--", TARGET_FILE], cwd=repo_root)
    if staged_cp.returncode == 0:
        return finish("NO_STAGED_INDEX_HTML_CHANGE", log_path)

    commit_cp = run_git(["commit", "-m", COMMIT_MESSAGE], cwd=repo_root)
    if commit_cp.returncode != 0:
        return finish("GIT_COMMIT_FAILED", log_path, commit_cp.stderr.strip() or "UNKNOWN")

    hash_cp = run_git(["rev-parse", "HEAD"], cwd=repo_root)
    commit_hash = hash_cp.stdout.strip() if hash_cp.returncode == 0 and hash_cp.stdout.strip() else "UNKNOWN"
    return finish("COMMIT_SUCCESS", log_path, commit_hash)


if __name__ == "__main__":
    raise SystemExit(main())
