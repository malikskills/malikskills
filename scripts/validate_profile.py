#!/usr/bin/env python3
"""Offline integrity checks for MALIK DEV profile sources and generated assets."""
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SVG_NS = "{http://www.w3.org/2000/svg}"
EXPECTED_SECTIONS = [
    "About Me", "Featured Projects", "Engineering Stack",
    "Engineering Approach", "GitHub Activity", "Connect",
]
THEMES = ("light", "dark")


class ReadmeMedia(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.paths: list[str] = []
        self.images = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "img":
            assert attributes.get("alt"), "Every README image requires meaningful alternative text"
            assert attributes.get("width") == "100%", "Every README image must fill the profile content width"
            assert attributes.get("src"), "README image has no source"
            self.images += 1
            self.paths.append(str(attributes["src"]))
        elif tag == "source":
            assert attributes.get("srcset"), "README picture source has no srcset"
            self.paths.append(str(attributes["srcset"]))


def fail(message: str) -> None:
    raise AssertionError(message)


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        fail(f"Invalid JSON in {path.relative_to(ROOT)}: {error}")


def validate_profile_data(profile: object) -> dict:
    assert isinstance(profile, dict), "profile.json root must be an object"
    for key in ("schema_version", "identity", "about", "contacts", "technology_groups", "projects", "colors", "illustrations", "statistics", "snake"):
        assert key in profile, f"profile.json lacks {key}"
    identity = profile["identity"]
    assert isinstance(identity, dict)
    for key in ("brand", "name", "github_username", "github_url", "location", "role", "positioning", "tagline"):
        assert isinstance(identity.get(key), str) and identity[key].strip(), f"identity.{key} must be a nonempty string"
    assert identity["github_username"] == "malikskills", "Configured GitHub identity must remain correct"
    assert identity["github_url"] == "https://github.com/malikskills", "Configured GitHub URL must remain correct"
    assert len(profile["about"]) == 4 and all(isinstance(line, str) and line for line in profile["about"])
    contacts = profile["contacts"]
    assert contacts["github"] == identity["github_url"]
    assert contacts["email"] is None, "Do not invent a contact email"
    assert len(profile["technology_groups"]) == 4
    labels = {group["label"] for group in profile["technology_groups"]}
    assert labels == {"Practiced foundations", "Used in project work", "Currently learning", "Areas of deeper study"}
    assert len(profile["projects"]) == 2
    for project in profile["projects"]:
        assert project["repository"] is None or str(project["repository"]).startswith("https://github.com/")
        assert project["repository_verification"] in {"verified_public", "pending_public_verification"}
    assert {item["slug"] for item in profile["projects"]} == {"dsie-learn", "plumier"}
    for theme in THEMES:
        palette = profile["colors"].get(theme)
        assert isinstance(palette, dict), f"Missing {theme} colour palette"
        for colour in ("background", "surface", "raised", "border", "foreground", "muted", "accent", "accent_secondary", "mint"):
            assert re.fullmatch(r"#[0-9A-Fa-f]{6}", str(palette.get(colour, ""))), f"Invalid {theme}.{colour} colour"
    return profile


def local_target(path: str) -> Path | None:
    parsed = urlsplit(path)
    if parsed.scheme or path.startswith("#"):
        return None
    if not parsed.path:
        return None
    candidate = (ROOT / unquote(parsed.path)).resolve()
    assert candidate.is_relative_to(ROOT), f"Path escapes the repository: {path}"
    return candidate


def validate_readme(profile: dict) -> ReadmeMedia:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    sections = re.findall(r"^## (.+)$", readme, re.MULTILINE)
    assert sections == EXPECTED_SECTIONS, "README must keep the banner and six editorial sections"
    assert profile["identity"]["name"] in readme
    assert profile["identity"]["github_url"] in readme
    for project in profile["projects"]:
        if project["repository_verification"] != "verified_public":
            for candidate in project["repository_candidates"]:
                assert f"/{candidate}" not in readme, f"Unverified repository must not be linked: {candidate}"
    parser = ReadmeMedia()
    parser.feed(readme)
    assert parser.images == 7, "Expected hero, two projects, stack, approach, activity and calendar images"
    assert len(parser.paths) == 26, "Responsive sources or theme variants are missing"
    assert readme.count("(max-width: 760px)") == 11, "Mobile picture sources must cover every responsive composition"
    assert readme.count("prefers-color-scheme: dark") == 12, "Dark theme sources must cover all theme-aware sections"
    assert "prefers-reduced-motion: reduce" in readme, "Contribution calendar needs a reduced-motion source"
    links = re.findall(r"\]\(([^)]+)\)", readme)
    for reference in parser.paths + links:
        target = local_target(reference)
        if target is not None:
            assert target.is_file(), f"Missing local resource: {reference}"
    assert all(urlsplit(path).scheme == "" for path in parser.paths), "README image sources must be self-contained"
    return parser


def validate_svg(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    assert "<!DOCTYPE" not in source and "<!ENTITY" not in source, f"Unsafe XML declaration in {path}"
    root = ET.fromstring(source)
    assert root.tag == SVG_NS + "svg" and root.get("viewBox"), f"Invalid SVG root: {path}"
    assert root.find(SVG_NS + "title") is not None, f"SVG has no title: {path}"
    assert root.find(SVG_NS + "desc") is not None, f"SVG has no description: {path}"
    forbidden = {"script", "foreignObject", "image", "iframe", "object", "embed"}
    for element in root.iter():
        name = element.tag.split("}")[-1]
        assert name not in forbidden, f"Unsupported SVG element {name}: {path}"
        for attribute, value in element.attrib.items():
            assert not attribute.lower().startswith("on"), f"Event handler in {path}"
            if attribute.endswith("href"):
                assert value.startswith("#"), f"External SVG reference in {path}"
    assert not re.search(r"@import|url\(\s*['\"]?https?://", source, re.I), f"Remote SVG resource in {path}"
    if path.name.startswith("contributions-"):
        assert "@keyframes" not in source and "<animate" not in source, f"Reduced-motion calendar is animated: {path}"


def validate_asset_matrix() -> list[Path]:
    expected = {
        "assets/branding/banner.svg", "assets/branding/banner-mobile.svg", "assets/branding/logo.svg", "assets/branding/engineering-map.svg",
        "assets/generated/activity.json", "assets/generated/activity.md",
    }
    for component in ("stack", "approach"):
        for theme in THEMES:
            expected.add(f"assets/branding/{component}-{theme}.svg")
            expected.add(f"assets/branding/{component}-mobile-{theme}.svg")
    for project in ("dsie-learn", "plumier"):
        for theme in THEMES:
            expected.add(f"assets/projects/{project}-{theme}.svg")
            expected.add(f"assets/projects/{project}-mobile-{theme}.svg")
    for theme in THEMES:
        for prefix in ("activity", "activity-mobile", "snake", "contributions"):
            expected.add(f"assets/generated/{prefix}-{theme}.svg")
    absent = sorted(item for item in expected if not (ROOT / item).is_file())
    assert not absent, f"Required generated or editorial assets missing: {', '.join(absent)}"
    svgs = sorted((ROOT / "assets").rglob("*.svg"))
    assert len(svgs) == 28, f"Expected exactly 28 SVG assets, found {len(svgs)}"
    for path in svgs:
        validate_svg(path)
    return svgs


def validate_snapshot(profile: dict) -> None:
    snapshot = read_json(ROOT / "assets/generated/activity.json")
    assert isinstance(snapshot, dict)
    assert snapshot.get("username") == profile["identity"]["github_username"]
    status = snapshot.get("status")
    assert status in {"success", "unavailable"}, "Unknown activity snapshot state"
    markdown = (ROOT / "assets/generated/activity.md").read_text(encoding="utf-8")
    if status == "success":
        counts = snapshot.get("language_counts")
        assert isinstance(counts, dict) and all(isinstance(value, int) and value >= 0 for value in counts.values())
        assert sum(counts.values()) == snapshot.get("repositories"), "Repository count does not equal language total"
        assert snapshot.get("primary_languages") == len([name for name in counts if name != "Not classified"])
        assert snapshot["updated"] in markdown
        for theme in THEMES:
            for prefix in ("activity", "activity-mobile"):
                assert snapshot["updated"] in (ROOT / f"assets/generated/{prefix}-{theme}.svg").read_text(encoding="utf-8")
    else:
        assert "repositories" not in snapshot and "language_counts" not in snapshot, "Unavailable snapshot must not contain invented counts"
        assert "No verified GitHub REST API snapshot" in markdown


def validate_workflows() -> None:
    workflows = sorted((ROOT / ".github/workflows").glob("*.yml"))
    assert {path.name for path in workflows} == {"snake.yml", "validate.yml"}, "Expected validation and refresh workflows"
    for path in workflows:
        content = path.read_text(encoding="utf-8")
        assert "pull_request_target" not in content and "write-all" not in content
        for action in re.findall(r"uses:\s*(\S+)", content):
            assert re.fullmatch(r"[\w./-]+@[0-9a-f]{40}", action), f"Unpinned action in {path}: {action}"
    refresh = (ROOT / ".github/workflows/snake.yml").read_text(encoding="utf-8")
    assert "PROFILE_AUTO_COMMIT" in refresh, "Automatic generated-art commits require an explicit repository variable"
    assert "github.event.inputs.publish == 'true'" in refresh, "Manual publication requires explicit input"


def validate() -> tuple[int, int]:
    profile = validate_profile_data(read_json(ROOT / "profile.json"))
    media = validate_readme(profile)
    svgs = validate_asset_matrix()
    validate_snapshot(profile)
    validate_workflows()
    return len(svgs), len(media.paths)


def main() -> None:
    try:
        svg_count, media_count = validate()
    except (AssertionError, ET.ParseError) as error:
        print(f"Profile validation failed: {error}", file=sys.stderr)
        raise SystemExit(1)
    print(f"Validated {svg_count} SVGs, {media_count} README picture sources, profile data, generated state and workflows")


if __name__ == "__main__":
    main()
