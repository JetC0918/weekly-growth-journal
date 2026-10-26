#!/usr/bin/env python3
"""Reject staged or tracked secret-bearing files before they leave the repo."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys


SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b"),
    re.compile(
        r"(?i)\b(?:api[_-]?key|client[_-]?secret|password|token|secret)\b"
        r"\s*[:=]\s*[\"']?[A-Za-z0-9/+_-]{32,}"
    ),
)
EXAMPLE_ENV_FILES = {".env.example", ".env.test.example"}


def git_output(*args: str) -> bytes:
    return subprocess.run(
        ["git", *args], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ).stdout


def staged_files() -> list[str]:
    return [p.decode("utf-8", "surrogateescape") for p in git_output(
        "diff", "--cached", "--name-only", "--diff-filter=ACMRT", "-z"
    ).split(b"\0") if p]


def tracked_files() -> list[str]:
    return [p.decode("utf-8", "surrogateescape") for p in git_output("ls-files", "-z").split(b"\0") if p]


def read_content(path: str, staged: bool) -> bytes:
    if staged:
        return git_output("show", f":{path}")
    with open(path, "rb") as file:
        return file.read()


def check(paths: list[str], staged: bool) -> list[str]:
    findings = []
    for path in paths:
        normalized = path.replace("\\", "/")
        basename = normalized.rsplit("/", 1)[-1]
        if (basename.startswith(".env") and basename not in EXAMPLE_ENV_FILES) or basename.endswith(
            (".pem", ".key", ".p12", ".pfx")
        ):
            findings.append(f"{path}: secret-bearing filename is not allowed")
            continue
        try:
            content = read_content(path, staged)
        except (OSError, subprocess.CalledProcessError) as error:
            findings.append(f"{path}: unable to inspect content ({error})")
            continue
        if b"\0" in content:
            continue
        decoded = content.decode("utf-8", "replace")
        for pattern in SECRET_PATTERNS:
            if pattern.search(decoded):
                findings.append(f"{path}: content matches a credential/private-key pattern")
                break
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tracked", action="store_true", help="scan all tracked files (for CI)"
    )
    args = parser.parse_args()
    paths = tracked_files() if args.tracked else staged_files()
    findings = check(paths, staged=not args.tracked)
    if findings:
        print("Staged-content guardrail failed:", file=sys.stderr)
        print("\n".join(f"- {finding}" for finding in findings), file=sys.stderr)
        return 1
    print(f"Staged-content guardrail passed ({len(paths)} file(s) checked).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
