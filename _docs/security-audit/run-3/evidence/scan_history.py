"""Read reachable Git blobs for high-confidence secret patterns; never print values."""
import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
spec = importlib.util.spec_from_file_location("guard", ROOT / "agent-hooks/check_staged_changes.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def main():
    objects = {}
    for row in git("rev-list", "--objects", "--all").decode("utf-8", "replace").splitlines():
        sha, _, name = row.partition(" ")
        objects.setdefault(sha, name)
    findings = []
    checked = binary = 0
    # Restrict the batch to blobs, avoiding commit metadata and trees.
    for sha, name in objects.items():
        if git("cat-file", "-t", sha).strip() != b"blob":
            continue
        data = git("cat-file", "blob", sha)
        checked += 1
        if b"\x00" in data:
            binary += 1
            continue
        text = data.decode("utf-8", "replace")
        for index, pattern in enumerate(guard.SECRET_PATTERNS, start=1):
            if pattern.search(text):
                findings.append({"blob": sha, "path": name, "pattern_number": index})
    result = {
        "base_revision": git("rev-parse", "HEAD").decode().strip(),
        "reachable_commits": int(git("rev-list", "--all", "--count")),
        "unique_blobs_checked": checked,
        "binary_blobs_skipped": binary,
        "matches": findings,
        "limitations": "High-confidence repository guard patterns only; no entropy scanner, unreachable objects, remote-only refs, LFS payloads or binary secrets. No secret values emitted.",
    }
    destination = Path(__file__).with_name("history-scan.json")
    destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
