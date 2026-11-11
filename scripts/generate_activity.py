#!/usr/bin/env python3
"""Fetch a conservative public-repository snapshot and render branded SVGs.

Only successful API responses can create numeric statistics.  Rendering happens
in memory before atomic replacements, so a failed refresh leaves the previous
valid snapshot untouched.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    from .artwork import activity, load_profile
except ImportError:  # Script invocation
    from artwork import activity, load_profile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "generated"
USERNAME_RE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38}[A-Za-z0-9])?$")


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def api_get(path: str) -> object:
    """Request a GitHub REST endpoint with the least authority available."""
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "malik-skills-profile-generator",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    for attempt in range(3):
        try:
            request = Request(f"https://api.github.com/{path}", headers=headers)
            with urlopen(request, timeout=30) as response:
                return json.load(response)
        except HTTPError as exc:
            retryable = exc.code in {429, 500, 502, 503, 504}
            if not retryable or attempt == 2:
                raise RuntimeError(f"GitHub API returned HTTP {exc.code}") from None
        except (URLError, TimeoutError) as exc:
            if attempt == 2:
                raise RuntimeError("GitHub API is unavailable; existing generated assets were retained") from exc
        time.sleep(2 ** attempt)
    raise AssertionError("unreachable retry loop")


def public_repositories(username: str, fetch=api_get) -> list[dict[str, str | None]]:
    """List all public, owned, non-fork repositories, preserving no duplicates."""
    if not USERNAME_RE.fullmatch(username):
        raise ValueError("Invalid GitHub username")
    by_id: dict[int | str, dict[str, str | None]] = {}
    page = 1
    while True:
        payload = fetch(f"users/{username}/repos?type=owner&per_page=100&page={page}")
        if not isinstance(payload, list):
            raise ValueError("GitHub repository response must be a list")
        for raw in payload:
            if not isinstance(raw, dict):
                raise ValueError("GitHub repository item must be an object")
            owner = raw.get("owner")
            if not isinstance(owner, dict):
                continue
            if raw.get("private") is False and raw.get("fork") is False and str(owner.get("login", "")).lower() == username.lower():
                identifier = raw.get("id")
                name, language = raw.get("name"), raw.get("language")
                if identifier is None or not isinstance(name, str) or not name:
                    raise ValueError("GitHub repository item misses a stable id or name")
                by_id[identifier] = {"name": name, "language": language if isinstance(language, str) else None}
        if len(payload) < 100:
            break
        page += 1
    return sorted(by_id.values(), key=lambda repo: str(repo["name"]).casefold())


def summarize(repositories: list[dict[str, str | None]], username: str, updated: str) -> dict[str, object]:
    counts = Counter((repo["language"] or "Not classified") for repo in repositories)
    languages = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return {
        "status": "success",
        "username": username,
        "updated": updated,
        "source": f"https://api.github.com/users/{username}/repos?type=owner&per_page=100",
        "scope": "Public repositories owned by the configured account; forks are excluded and archived originals are included.",
        "repositories": len(repositories),
        "primary_languages": len([language for language in counts if language != "Not classified"]),
        "language_counts": dict(languages),
    }


def unavailable_snapshot(username: str, reason: str | None = None) -> dict[str, object]:
    """A transparent bootstrap state, intentionally without statistics."""
    return {
        "status": "unavailable",
        "username": username,
        "last_attempt": iso_now(),
        "reason": reason or "No successful GitHub REST API snapshot has been recorded yet.",
        "scope": "No repository or language counts are shown until a successful public GitHub API refresh.",
    }


def snapshot_markdown(snapshot: dict[str, object]) -> str:
    if snapshot["status"] != "success":
        return "\n".join([
            "# Public repository snapshot", "",
            "No verified GitHub REST API snapshot has been published yet.", "",
            f"- Last attempt: **{snapshot['last_attempt']}**.",
            f"- Reason: {snapshot['reason']}", "",
            "Repository counts, language counts and contribution totals are intentionally omitted. "
            "Run `python3 scripts/generate_activity.py` with network access, or run the configured GitHub Actions workflow.", "",
        ])
    rows = snapshot["language_counts"]
    assert isinstance(rows, dict)
    return "\n".join([
        "# Public repository snapshot", "",
        f"Updated **{snapshot['updated']} UTC** from the GitHub REST API.", "",
        f"- Original public repositories: **{snapshot['repositories']}**.",
        f"- Distinct primary languages: **{snapshot['primary_languages']}**.", "",
        "| Primary language | Repositories |", "| --- | ---: |",
        *[f"| {language} | {count} |" for language, count in rows.items()], "",
        str(snapshot["scope"]), "",
        "GitHub assigns one primary language to each repository. These repository counts do not measure proficiency, "
        "all languages used, lines of code, commits or project completion.", "",
        f"[Source]({snapshot['source']}). Pagination is followed. A failed later refresh keeps the last valid files.", "",
    ])


def render_files(snapshot: dict[str, object], profile: dict[str, object]) -> dict[str, str]:
    files = {
        f"activity-{'mobile-' if mobile else ''}{theme}.svg": activity(snapshot, theme == "dark", mobile, profile)
        for theme in ("light", "dark") for mobile in (False, True)
    }
    files["activity.json"] = json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n"
    files["activity.md"] = snapshot_markdown(snapshot)
    return files


def write_all(files: dict[str, str], output: Path = OUTPUT) -> None:
    """Stage all content before any final path is replaced."""
    output.mkdir(parents=True, exist_ok=True)
    temporaries: list[tuple[Path, Path]] = []
    try:
        for name, content in files.items():
            destination = output / name
            temporary = output / f".{name}.tmp"
            temporary.write_text(content, encoding="utf-8")
            temporaries.append((temporary, destination))
        for temporary, destination in temporaries:
            temporary.replace(destination)
    finally:
        for temporary, _ in temporaries:
            if temporary.exists():
                temporary.unlink()


def generate() -> dict[str, object]:
    profile = load_profile(ROOT)
    identity = profile["identity"]
    assert isinstance(identity, dict)
    username = str(identity["github_username"])
    repositories = public_repositories(username)
    snapshot = summarize(repositories, username, datetime.now(timezone.utc).date().isoformat())
    write_all(render_files(snapshot, profile))
    return snapshot


def bootstrap(reason: str) -> dict[str, object]:
    profile = load_profile(ROOT)
    identity = profile["identity"]
    assert isinstance(identity, dict)
    snapshot = unavailable_snapshot(str(identity["github_username"]), reason)
    write_all(render_files(snapshot, profile))
    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate only real public GitHub repository statistics.")
    parser.add_argument("--bootstrap-unavailable", metavar="REASON", help="create a truthful, count-free initial state")
    args = parser.parse_args()
    if args.bootstrap_unavailable:
        snapshot = bootstrap(args.bootstrap_unavailable)
        print("Wrote a transparent unavailable snapshot; no statistics were invented")
        return
    try:
        snapshot = generate()
    except (RuntimeError, ValueError) as error:
        print(f"Activity refresh failed: {error}", file=sys.stderr)
        raise SystemExit(1)
    print(f"Updated verified public snapshot: {snapshot['repositories']} original repositories")


if __name__ == "__main__":
    main()
