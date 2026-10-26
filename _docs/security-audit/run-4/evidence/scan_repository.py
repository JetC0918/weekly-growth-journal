"""Scan tracked content and reachable Git blobs without displaying matched values."""
import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
spec = importlib.util.spec_from_file_location("guard", ROOT / "agent-hooks/check_staged_changes.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.PIPE)


paths = guard.tracked_files()
tracked_matches = guard.check(paths, staged=False)
objects = {}
for row in git("rev-list", "--objects", "--all").decode("utf-8", "replace").splitlines():
    sha, _, name = row.partition(" ")
    objects.setdefault(sha, name)
matches = []
checked = binary = 0
for sha, name in objects.items():
    if git("cat-file", "-t", sha).strip() != b"blob":
        continue
    data = git("cat-file", "blob", sha)
    checked += 1
    if b"\0" in data:
        binary += 1
        continue
    text = data.decode("utf-8", "replace")
    for index, pattern in enumerate(guard.SECRET_PATTERNS, 1):
        if pattern.search(text):
            matches.append({"blob": sha, "path": name, "pattern_number": index})
result = {
    "base_revision": git("rev-parse", "HEAD").decode().strip(),
    "tracked_files": len(paths),
    "tracked_matches": tracked_matches,
    "reachable_commits": int(git("rev-list", "--all", "--count")),
    "unique_blobs_checked": checked,
    "binary_blobs_skipped": binary,
    "history_matches": matches,
    "limitations": "Repository guard regex patterns only; not entropy scanning, binary scanning, LFS, unreachable objects, or remote-only history. No matched values displayed.",
}
Path(__file__).with_name("repository-secret-scan.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
