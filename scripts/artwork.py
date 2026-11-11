#!/usr/bin/env python3
"""Original, standard-library SVG artwork for the MALIK SKILLS profile.

The module is deliberately data-driven: profile.json owns wording, colours and
layout constants, while this file owns drawing primitives and compositions.
"""
from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

ICON_PATHS = {
    "compass": "M4 4L35 14L24 35L4 4ZM13 13L24 24",
    "chart": "M3 35V20H11V35M16 35V8H24V35M29 35V14H37V35",
    "blocks": "M12 1H26V13H12ZM1 26H13V38H1ZM26 26H38V38H26ZM19 13V20H7V26M19 20H32V26",
    "code": "M11 4L2 19L11 34M28 4L37 19L28 34M23 1L15 37",
    "check": "M3 20L14 31L36 5",
    "launch": "M3 35H37M20 28V2M8 14L20 2L32 14",
    "server": "M3 4H37V16H3ZM3 23H37V35H3M10 10H12M10 29H12",
    "database": "M2 7C2 -1 38 -1 38 7V31C38 39 2 39 2 31ZM2 7C2 15 38 15 38 7M2 20C2 28 38 28 38 20",
    "terminal": "M3 4H37V34H3ZM10 12L17 19L10 26M22 26H31",
    "cloud": "M9 31H31C39 31 40 18 31 17C28 5 10 6 9 17C0 18 1 31 9 31",
}


def load_profile(root: Path = ROOT) -> dict[str, Any]:
    """Read the one public source of truth, without accepting implicit defaults."""
    return json.loads((root / "profile.json").read_text(encoding="utf-8"))


def theme_tokens(profile: dict[str, Any], theme: str) -> dict[str, str]:
    colours = profile["colors"][theme]
    return {
        "bg": colours["background"], "surface": colours["surface"],
        "raised": colours["raised"], "border": colours["border"],
        "fg": colours["foreground"], "muted": colours["muted"],
        "accent": colours["accent"], "secondary": colours["accent_secondary"],
        "mint": colours["mint"],
    }


class Canvas:
    """Tiny safe SVG writer used instead of a framework or template engine."""

    def __init__(self, width: int, height: int, theme: str, title: str, desc: str,
                 profile: dict[str, Any], framed: bool = True) -> None:
        self.width, self.height = width, height
        self.colour = theme_tokens(profile, theme)
        self.font = profile["illustrations"]["font_family"]
        self.parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
            f'<title id="title">{escape(title)}</title>',
            f'<desc id="desc">{escape(desc)}</desc>',
        ]
        if framed:
            self.rect(1, 1, width - 2, height - 2, "bg", "border", 24)

    def c(self, value: str) -> str:
        return self.colour.get(value, value)

    def raw(self, markup: str) -> None:
        self.parts.append(markup)

    def rect(self, x: float, y: float, width: float, height: float,
             fill: str = "surface", stroke: str = "border", radius: float = 16,
             stroke_width: float = 2) -> None:
        self.parts.append(
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" '
            f'fill="{self.c(fill)}" stroke="{self.c(stroke)}" stroke-width="{stroke_width}"/>'
        )

    def text(self, x: float, y: float, value: Any, size: float = 28,
             colour: str = "fg", weight: int = 400, anchor: str = "start") -> None:
        self.parts.append(
            f'<text x="{x}" y="{y}" font-family="{escape(self.font)}" font-size="{size}" '
            f'font-weight="{weight}" text-anchor="{anchor}" fill="{self.c(colour)}">'
            f'{escape(str(value))}</text>'
        )

    def path(self, data: str, colour: str = "border", width: float = 2,
             fill: str = "none") -> None:
        self.parts.append(
            f'<path d="{data}" fill="{self.c(fill)}" stroke="{self.c(colour)}" '
            f'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>'
        )

    def dot(self, x: float, y: float, radius: float = 4, colour: str = "accent") -> None:
        self.parts.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{self.c(colour)}"/>')

    def icon(self, name: str, x: float, y: float, scale: float = 1.0,
             colour: str = "accent") -> None:
        self.raw(f'<g transform="translate({x} {y}) scale({scale})">')
        self.path(ICON_PATHS[name], colour, 2.5)
        self.raw("</g>")

    def finish(self) -> str:
        return "\n".join(self.parts + ["</svg>"]) + "\n"

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.finish(), encoding="utf-8")


def hero(profile: dict[str, Any], mobile: bool = False) -> str:
    identity = profile["identity"]
    w, h = (480, 320) if mobile else (1200, 400)
    canvas = Canvas(
        w, h, "dark", "MALIK SKILLS / Engineering Reliable Digital Solutions",
        "Tiayon Malik, junior web developer in Cameroon, focuses on backend-oriented development with Python and Django. A clear MS monogram connects software-system nodes.",
        profile,
    )
    canvas.raw(
        '<defs><linearGradient id="signal" x1="0" x2="1" y1="0" y2="1">'
        f'<stop stop-color="{canvas.c("accent")}"/><stop offset="1" stop-color="{canvas.c("secondary")}"/>'
        '</linearGradient></defs>'
    )
    if mobile:
        canvas.text(28, 54, identity["brand"], 48, weight=700)
        canvas.text(28, 99, "Engineering Reliable", 27)
        canvas.text(28, 134, "Digital Solutions", 27)
        canvas.text(28, 207, "Junior Web Developer", 23, "muted")
        canvas.text(28, 242, "Python · Django · Backend", 23, "muted")
        canvas.path("M28 281H452", "border")
        canvas.path("M28 281H138", "accent", 3)
        monogram(canvas, 350, 53, 0.65)
    else:
        canvas.text(56, 68, "MALIK SKILLS / BACKEND-ORIENTED DEVELOPMENT", 23, "muted", 700)
        canvas.text(52, 184, identity["brand"], 96, weight=700)
        canvas.text(56, 247, identity["tagline"], 37)
        canvas.text(56, 324, "Junior Web Developer · Python & Django · Cameroon", 27, "muted")
        canvas.path("M56 364H696", "border")
        canvas.path("M56 364H190", "accent", 3)
        system_nodes(canvas)
        monogram(canvas, 861, 132, 1.15)
    return canvas.finish()


def monogram(canvas: Canvas, x: int, y: int, scale: float) -> None:
    canvas.raw(f'<g transform="translate({x} {y}) scale({scale})">')
    canvas.rect(0, 0, 126, 126, "surface", "secondary", 24)
    canvas.text(63, 84, "MS", 58, "accent", 700, "middle")
    canvas.dot(108, 19, 4, "mint")
    canvas.raw("</g>")


def system_nodes(canvas: Canvas) -> None:
    canvas.path("M752 76H817V164H861M1045 80V122H994M996 220H1111V300H1064M766 311H819V252H861")
    for x, y, colour in [(730, 54, "accent"), (1023, 58, "mint"), (1042, 278, "accent"), (744, 289, "mint")]:
        canvas.rect(x, y, 44, 44, "surface")
        canvas.dot(x + 22, y + 22, 4, colour)
    canvas.dot(817, 164, 4, "accent")
    canvas.dot(1111, 220, 4, "accent")
    canvas.dot(819, 252, 4, "mint")


def project_card(profile: dict[str, Any], slug: str, theme: str, mobile: bool) -> str:
    project = next(item for item in profile["projects"] if item["slug"] == slug)
    is_dsie = slug == "dsie-learn"
    title = project["name"]
    w, h = (480, 420) if mobile else (1200, 420)
    description = (
        "Original conceptual diagram for DSIE Learn. It does not represent a deployed interface."
        if is_dsie else "Original conceptual diagram for Plumier. It does not represent a deployed interface."
    )
    canvas = Canvas(w, h, theme, f"{title} / Product concept", description, profile)
    eyebrow = "01 / EDTECH · IN PROGRESS" if is_dsie else "02 / SCHOOL SYSTEM · IN PROGRESS"
    repository_caption = "Public repos: backend + frontend" if is_dsie else "Repository URL pending verification"
    if mobile:
        canvas.text(28, 42, eyebrow, 19, "muted", 700)
        canvas.text(28, 95, title, 40, weight=700)
        mobile_lines = (
            ["Learn digital skills.", "Built for useful progress."]
            if is_dsie else ["School operations, modular.", "Built to evolve carefully."]
        )
        for index, line in enumerate(mobile_lines):
            canvas.text(28, 140 + index * 33, line, 23)
        canvas.text(28, 212, "Python · Django · PostgreSQL", 21, "muted")
        if is_dsie:
            dsie_diagram(canvas, 28, 239, True)
        else:
            plumier_diagram(canvas, 28, 239, True)
        canvas.text(28, 390, repository_caption, 21, "accent", 700)
    else:
        canvas.text(56, 63, eyebrow, 23, "muted", 700)
        canvas.text(56, 143, title, 62, weight=700)
        lines = (
            ["Digital-skills learning, shaped for", "Cameroon and Francophone Africa."]
            if is_dsie else ["School management with modular", "foundations for daily operations."]
        )
        for index, line in enumerate(lines):
            canvas.text(56, 201 + index * 39, line, 27)
        stack_line = "Django · DRF · PostgreSQL" if is_dsie else "Django · PostgreSQL · Allauth"
        canvas.text(56, 296, stack_line, 23, "muted")
        extra = "Next.js target · Infrastructure planned" if is_dsie else "Modules developed iteratively"
        canvas.text(56, 329, extra, 23, "muted")
        canvas.text(56, 381, repository_caption, 25, "accent", 700)
        if is_dsie:
            dsie_diagram(canvas, 602, 68, False)
        else:
            plumier_diagram(canvas, 602, 68, False)
    return canvas.finish()


def dsie_diagram(canvas: Canvas, x: int, y: int, mobile: bool) -> None:
    canvas.raw(f'<g transform="translate({x} {y})">')
    if mobile:
        canvas.rect(0, 0, 424, 106)
        canvas.text(17, 27, "LEARNING PATH / CONCEPT", 17, "muted", 700)
        for px, label in [(18, "Explore"), (152, "Practice"), (286, "Grow")]:
            canvas.rect(px, 50, 118, 35, "bg", "border", 10)
            canvas.text(px + 59, 73, label, 17, anchor="middle")
        canvas.path("M136 67H151M270 67H285", "accent", 2.5)
    else:
        canvas.rect(0, 0, 542, 276)
        canvas.text(24, 39, "LEARNING SYSTEM / CONCEPT", 21, "muted", 700)
        canvas.path("M0 61H542")
        canvas.icon("cloud", 28, 89, 1.05)
        canvas.text(86, 108, "Skills pathway", 27, weight=700)
        canvas.text(86, 140, "Guided progress, practical learning", 20, "muted")
        for index, (label, detail) in enumerate([("Discover", "courses"), ("Practice", "projects"), ("Advance", "feedback")]):
            px = 26 + index * 166
            canvas.rect(px, 183, 138, 62, "bg", "accent" if index == 1 else "border", 12)
            canvas.text(px + 14, 211, label, 21, weight=700)
            canvas.text(px + 14, 233, detail, 17, "muted")
            if index < 2:
                canvas.path(f"M{px + 139} 214H{px + 165}", "accent", 2.5)
        canvas.dot(486, 101, 7, "mint")
        canvas.dot(514, 101, 7, "accent")
    canvas.raw("</g>")


def plumier_diagram(canvas: Canvas, x: int, y: int, mobile: bool) -> None:
    canvas.raw(f'<g transform="translate({x} {y})">')
    if mobile:
        canvas.rect(0, 0, 424, 106)
        canvas.text(17, 27, "SCHOOL MODULES / CONCEPT", 17, "muted", 700)
        for px, label in [(18, "People"), (152, "Classes"), (286, "Records")]:
            canvas.rect(px, 50, 118, 35, "bg", "border", 10)
            canvas.text(px + 59, 73, label, 17, anchor="middle")
        canvas.path("M136 67H151M270 67H285", "accent", 2.5)
    else:
        canvas.rect(0, 0, 542, 276)
        canvas.text(24, 39, "SCHOOL OPERATIONS / CONCEPT", 21, "muted", 700)
        canvas.path("M0 61H542")
        canvas.rect(29, 94, 164, 139, "bg")
        canvas.icon("blocks", 47, 114, .95)
        canvas.text(99, 129, "Core", 25, weight=700)
        for row, label in enumerate(["People", "Classes", "Access"]):
            canvas.path(f"M48 {165 + row * 21}H171", "muted", 3)
            canvas.dot(48, 165 + row * 21, 3, "accent")
            canvas.text(62, 171 + row * 21, label, 17, "muted")
        canvas.path("M193 163H238V107H269M238 163H269M238 163V220H269", "accent", 2.5)
        for py, label in [(77, "Academic records"), (139, "Attendance"), (201, "Finance")]:
            canvas.rect(269, py, 244, 45, "surface", "border", 11)
            canvas.text(289, py + 29, label, 20, weight=700)
        canvas.dot(238, 163, 4, "mint")
    canvas.raw("</g>")


def stack_map(profile: dict[str, Any], theme: str, mobile: bool) -> str:
    width, height = (480, 670) if mobile else (1200, 510)
    canvas = Canvas(
        width, height, theme, "MALIK SKILLS / Technology landscape",
        "A candid technology landscape: practiced foundations, project-context tools, current learning and engineering interests. It is not a proficiency ranking.", profile,
    )
    cards = [
        ("BACKEND", "Practiced", "Python · Django · REST APIs", "server"),
        ("FRONTEND", "Foundations", "HTML · CSS · JavaScript", "code"),
        ("DATABASE", "Practiced", "PostgreSQL · data modelling", "database"),
        ("INFRA & DEVOPS", "Project context", "Docker · Compose · Linux", "cloud"),
        ("TOOLS", "Practice & study", "Git · GitHub · Ubuntu", "terminal"),
    ]
    if mobile:
        canvas.text(28, 42, "TECHNOLOGY LANDSCAPE / HONEST SCOPE", 18, "muted", 700)
        for index, (label, state, items, icon) in enumerate(cards):
            y = 67 + index * 112
            canvas.rect(28, y, 424, 94, "surface", "accent" if label == "BACKEND" else "border", 14)
            canvas.icon(icon, 45, y + 19, .62)
            canvas.text(92, y + 32, label, 21, "muted", 700)
            canvas.text(92, y + 57, state, 23, weight=700)
            canvas.text(45, y + 81, items, 18, "muted")
        canvas.text(28, 643, "Interests: architecture · CI/CD · networking", 18, "muted")
    else:
        canvas.text(56, 56, "TECHNOLOGY LANDSCAPE / HONEST SCOPE", 23, "muted", 700)
        positions = [(56, 91, 342), (429, 91, 342), (802, 91, 342), (242, 285, 342), (615, 285, 342)]
        for index, ((label, state, items, icon), (x, y, w)) in enumerate(zip(cards, positions)):
            canvas.rect(x, y, w, 153, "surface", "accent" if label == "BACKEND" else "border", 16)
            canvas.text(x + 24, y + 39, label, 21, "muted", 700)
            canvas.icon(icon, x + w - 59, y + 25, .75)
            canvas.text(x + 24, y + 82, state, 30, weight=700)
            canvas.text(x + 24, y + 119, items, 20, "muted")
        canvas.text(56, 480, "Current study: TypeScript · Tailwind CSS · Redis · Celery · Nginx · architecture · DevOps", 22, "muted")
    return canvas.finish()


def approach(profile: dict[str, Any], theme: str, mobile: bool) -> str:
    width, height = (480, 360) if mobile else (1200, 260)
    canvas = Canvas(
        width, height, theme, "Discover → Analyze → Architect → Build → Validate → Deliver",
        "Six-step working method: understand a need, examine constraints, shape the design, implement deliberately, validate behaviour and deliver safely.", profile, framed=False,
    )
    # A deliberate opaque artboard keeps the light and dark variants reliable in
    # GitHub's image renderer and in standalone SVG viewers.
    canvas.rect(0, 0, width, height, "bg", "bg", 0, 0)
    steps = [
        ("Discover", "Understand needs", "compass"),
        ("Analyze", "Map constraints", "chart"),
        ("Architect", "Shape boundaries", "blocks"),
        ("Build", "Implement clearly", "code"),
        ("Validate", "Test behaviour", "check"),
        ("Deliver", "Release carefully", "launch"),
    ]
    if mobile:
        canvas.path("M240 25V333", "border")
        for index, (name, caption, icon) in enumerate(steps):
            column, row = index % 2, index // 2
            x, y = 28 + column * 226, 26 + row * 112
            canvas.text(x, y + 22, f"0{index + 1}", 19, "accent", 700)
            canvas.icon(icon, x + 147, y + 2, .62)
            canvas.text(x, y + 62, name, 26, weight=700)
            canvas.text(x, y + 88, caption, 18, "muted")
    else:
        canvas.path("M80 104H1120", "accent")
        for index, (name, caption, icon) in enumerate(steps):
            x = 56 + index * 184
            canvas.icon(icon, x + 9, 28, .83)
            canvas.dot(x + 24, 104, 20, "surface")
            canvas.dot(x + 24, 104, 5, "accent")
            canvas.text(x + 53, 78, f"0{index + 1}", 23, "accent", 700)
            canvas.text(x, 168, name, 29, weight=700)
            canvas.text(x, 209, caption, 20, "muted")
    return canvas.finish()


def activity(snapshot: dict[str, Any], dark: bool, mobile: bool = False,
             profile: dict[str, Any] | None = None) -> str:
    """Draw exactly one validated snapshot at desktop or mobile scale."""
    profile = profile or load_profile()
    theme = "dark" if dark else "light"
    success = snapshot.get("status") == "success"
    counts = snapshot.get("language_counts", {}) if success else {}
    row_count = max(1, len(counts))
    width = 480 if mobile else 1200
    height = max(400, 224 + row_count * 30) if mobile else max(340, 126 + row_count * 34)
    title = "Public GitHub / Repository snapshot"
    if success:
        desc = (
            f"Updated {snapshot['updated']} UTC. {snapshot['repositories']} public original repositories, "
            f"forks excluded; {snapshot['primary_languages']} primary languages. Repository counts are not proficiency or code-volume measures."
        )
    else:
        desc = "No verified GitHub snapshot is available yet. The dashboard intentionally omits counts rather than inventing statistics."
    canvas = Canvas(width, height, theme, title, desc, profile)
    if not success:
        return unavailable_activity(canvas, mobile, snapshot)
    rows = sorted(counts.items(), key=lambda item: (item[0] == "Not classified", -item[1], item[0]))
    maximum = max(counts.values(), default=1)
    if mobile:
        canvas.text(28, 39, "PUBLIC GITHUB / VERIFIED SNAPSHOT", 20, "muted", 700)
        canvas.text(28, 96, snapshot["repositories"], 44, weight=700)
        canvas.text(258, 96, snapshot["primary_languages"], 44, weight=700)
        canvas.text(28, 127, "Original public repos", 20, "muted")
        canvas.text(258, 127, "Primary languages", 20, "muted")
        canvas.path("M28 149H452")
        canvas.text(28, 184, "Repositories by primary language", 22, weight=700)
        for index, (language, number) in enumerate(rows):
            y = 216 + index * 30
            canvas.text(28, y, language, 20)
            canvas.rect(204, y - 14, 194, 9, "raised", "raised", 4, 0)
            canvas.rect(204, y - 14, 194 * number / maximum, 9, "accent", "accent", 4, 0)
            canvas.text(428, y, number, 20)
        canvas.text(28, height - 18, f"Updated {snapshot['updated']} UTC · Forks excluded", 17, "muted")
    else:
        canvas.text(56, 52, "PUBLIC GITHUB / VERIFIED SNAPSHOT", 23, "muted", 700)
        canvas.text(56, 132, snapshot["repositories"], 63, weight=700)
        canvas.text(288, 132, snapshot["primary_languages"], 63, weight=700)
        canvas.text(56, 174, "Original public", 25, "muted")
        canvas.text(56, 207, "repositories", 25, "muted")
        canvas.text(288, 174, "Primary", 25, "muted")
        canvas.text(288, 207, "languages", 25, "muted")
        canvas.path(f"M521 48V{height - 60}")
        canvas.text(565, 52, "REPOSITORIES BY PRIMARY LANGUAGE", 23, "muted", 700)
        for index, (language, number) in enumerate(rows):
            y = 96 + index * 34
            canvas.text(565, y, language, 24)
            canvas.rect(778, y - 16, 310, 12, "raised", "raised", 6, 0)
            canvas.rect(778, y - 16, 310 * number / maximum, 12, "accent", "accent", 6, 0)
            canvas.text(1113, y, number, 24)
        canvas.text(56, height - 25, f"Updated {snapshot['updated']} UTC • Forks excluded", 23, "muted")
        canvas.text(778, height - 25, "Definitions linked below ↘", 23, "accent")
    return canvas.finish()


def unavailable_activity(canvas: Canvas, mobile: bool, snapshot: dict[str, Any]) -> str:
    label = "AWAITING FIRST VERIFIED API SNAPSHOT"
    attempt = snapshot.get("last_attempt", "not yet attempted")
    if mobile:
        canvas.text(28, 44, "PUBLIC GITHUB / SNAPSHOT", 21, "muted", 700)
        canvas.icon("cloud", 28, 91, 1.2)
        canvas.text(88, 116, "No verified statistics yet", 28, weight=700)
        canvas.text(28, 178, "Counts are intentionally omitted until", 21, "muted")
        canvas.text(28, 208, "the GitHub REST API refresh succeeds.", 21, "muted")
        canvas.rect(28, 252, 424, 64, "surface", "accent", 14)
        canvas.text(48, 280, label, 16, "accent", 700)
        canvas.text(48, 304, f"Last attempt: {attempt}", 16, "muted")
        canvas.text(28, 372, "Existing successful snapshots are never replaced on failure.", 15, "muted")
    else:
        canvas.text(56, 53, "PUBLIC GITHUB / SNAPSHOT", 23, "muted", 700)
        canvas.icon("cloud", 56, 102, 1.35)
        canvas.text(126, 133, "No verified statistics published yet", 39, weight=700)
        canvas.text(56, 188, "Repository counts and language distribution appear only after a successful GitHub REST API refresh.", 24, "muted")
        canvas.rect(56, 224, 1088, 67, "surface", "accent", 15)
        canvas.text(82, 255, label, 20, "accent", 700)
        canvas.text(82, 279, f"Last attempt: {attempt}. Existing successful snapshots are retained if a later refresh fails.", 19, "muted")
        canvas.text(56, 322, "No values are inferred from profile text, planned projects or technology interests.", 20, "muted")
    return canvas.finish()


def logo(profile: dict[str, Any]) -> str:
    canvas = Canvas(128, 128, "dark", "MALIK SKILLS monogram", "Clear MS monogram for MALIK SKILLS.", profile)
    canvas.text(64, 85, "MS", 58, "accent", 700, "middle")
    canvas.dot(108, 19, 4, "mint")
    return canvas.finish()


def engineering_map(profile: dict[str, Any]) -> str:
    canvas = Canvas(
        560, 160, "dark", "Reliable solution map",
        "Interfaces feed backend services and data. Delivery foundations support the system. This is a focus map, not a skill rating.", profile,
    )
    canvas.path("M154 54H211M349 54H406M84 83V116H476V83M280 83V116")
    for x, label, accent in [(22, "Interfaces", "border"), (211, "Backend", "accent"), (406, "Data", "border")]:
        canvas.rect(x, 26, 132 if x != 211 else 138, 56, "surface", accent, 8)
        center = x + (66 if x != 211 else 69)
        canvas.text(center, 61, label, 18, anchor="middle")
    canvas.text(280, 144, "Reliable delivery foundations", 16, "muted", anchor="middle")
    canvas.dot(182, 54, 3, "accent")
    canvas.dot(377, 54, 3, "accent")
    canvas.dot(280, 116, 3, "mint")
    return canvas.finish()


def build_editorial_assets(root: Path = ROOT) -> None:
    profile = load_profile(root)
    brand = root / "assets" / "branding"
    projects = root / "assets" / "projects"
    (brand / "banner.svg").write_text(hero(profile), encoding="utf-8")
    (brand / "banner-mobile.svg").write_text(hero(profile, True), encoding="utf-8")
    (brand / "logo.svg").write_text(logo(profile), encoding="utf-8")
    (brand / "engineering-map.svg").write_text(engineering_map(profile), encoding="utf-8")
    for theme in ("light", "dark"):
        for mobile in (False, True):
            suffix = f"{'mobile-' if mobile else ''}{theme}"
            (projects / f"dsie-learn-{suffix}.svg").write_text(
                project_card(profile, "dsie-learn", theme, mobile), encoding="utf-8")
            (projects / f"plumier-{suffix}.svg").write_text(
                project_card(profile, "plumier", theme, mobile), encoding="utf-8")
            (brand / f"stack-{suffix}.svg").write_text(stack_map(profile, theme, mobile), encoding="utf-8")
            (brand / f"approach-{suffix}.svg").write_text(approach(profile, theme, mobile), encoding="utf-8")


if __name__ == "__main__":
    build_editorial_assets()
    print("Built MALIK SKILLS editorial SVG assets")
