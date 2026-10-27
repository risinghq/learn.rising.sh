"""Downloads the original Qiskit/documentation guides into .cache/qiskit-docs.

    python tools/fetch_docs.py

Fetches only docs/guides, at the version pinned in tools/qiskit-docs.commit.
If .cache/qiskit-docs is already at that version, it does nothing.
build.py and extract.py read from here. To update the guides, change the hash in
tools/qiskit-docs.commit and run it again.
"""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / ".cache" / "qiskit-docs"
PIN = Path(__file__).resolve().parent / "qiskit-docs.commit"
REPO = "https://github.com/Qiskit/documentation.git"


def git(*args: str, capture: bool = False) -> str:
    return subprocess.run(
        ["git", "-C", str(DEST), *args], check=True, text=True, capture_output=capture
    ).stdout


def current() -> str | None:
    try:
        return git("rev-parse", "HEAD", capture=True).strip()
    except subprocess.CalledProcessError, FileNotFoundError:
        return None


def main() -> None:
    commit = PIN.read_text(encoding="utf-8").strip()
    if current() == commit and (DEST / "docs" / "guides" / "_toc.json").exists():
        print(f"guides up to date: {commit[:8]}")
        return
    DEST.mkdir(parents=True, exist_ok=True)
    if not (DEST / ".git").exists():
        git("init", "--quiet")
        git("remote", "add", "origin", REPO)
    git("sparse-checkout", "set", "docs/guides")
    git("fetch", "--quiet", "--depth", "1", "--filter=blob:none", "origin", commit)
    git("checkout", "--quiet", "--force", commit)
    print(f"guides downloaded: {commit[:8]} in {DEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
