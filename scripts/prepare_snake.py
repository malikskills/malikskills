#!/usr/bin/env python3
"""Turn Platane/snk output into accessible animated and static calendar assets."""
from __future__ import annotations

import argparse
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

try:
    from .artwork import load_profile, theme_tokens
except ImportError:  # Script invocation
    from artwork import load_profile, theme_tokens

ROOT = Path(__file__).resolve().parents[1]
NS = "http://www.w3.org/2000/svg"
Q = f"{{{NS}}}"
ET.register_namespace("", NS)


def today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _style_variables(css: str) -> tuple[dict[str, str], dict[str, str]]:
    variables = dict(re.findall(r"--([a-z0-9]+)\s*:\s*([^;}]+)", css))
    classes = dict(re.findall(r"\.c\.([a-z0-9]+)\s*\{[^}]*fill:var\(--([a-z0-9]+)\)", css))
    return variables, classes


def prepare(source: str, updated: str, brand: str = "MALIK DEV") -> tuple[str, str]:
    """Return an accessible animated SVG plus a genuine static grid SVG.

    Unknown upstream markup is rejected so it cannot silently publish a blank or
    misleading accessibility fallback.
    """
    root = ET.fromstring(source)
    if root.tag != Q + "svg":
        raise ValueError("Snake source is not an SVG")
    style = root.find(Q + "style")
    if style is None or not style.text:
        raise ValueError("Snake SVG has no stylesheet")
    variables, fills = _style_variables(style.text)
    cells = [element for element in root if element.tag == Q + "rect" and "c" in element.get("class", "").split()]
    if not 350 <= len(cells) <= 378 or "ce" not in variables:
        raise ValueError("Unexpected snake contribution-grid format; retain the previous valid calendar")
    for child in list(root):
        if child.tag in {Q + "title", Q + "desc"}:
            root.remove(child)
    root.set("role", "img")
    root.set("aria-labelledby", "title desc")
    title = ET.Element(Q + "title", {"id": "title"})
    title.text = f"{brand} GitHub contribution calendar"
    desc = ET.Element(Q + "desc", {"id": "desc"})
    desc.text = (
        f"Updated {updated} UTC. Daily contribution levels from GitHub, generated with "
        "https://github.com/Platane/snk. Private contribution visibility follows the GitHub profile setting."
    )
    root.insert(0, title)
    root.insert(1, desc)
    if "prefers-reduced-motion" not in style.text:
        style.text += "@media(prefers-reduced-motion:reduce){.c{animation:none!important}.s,.u{display:none}}"
    animated = ET.tostring(root, encoding="unicode") + "\n"

    static = ET.Element(Q + "svg", root.attrib)
    static.set("role", "img")
    static.set("aria-labelledby", "title desc")
    static.extend([deepcopy(title), deepcopy(desc)])
    for cell in cells:
        flat = deepcopy(cell)
        classes = flat.get("class", "").split()
        level = classes[1] if len(classes) > 1 else ""
        variable = fills.get(level, "ce")
        if variable not in variables:
            raise ValueError("Snake stylesheet is missing a referenced contribution colour")
        flat.attrib.pop("class", None)
        flat.set("width", "12")
        flat.set("height", "12")
        flat.set("fill", variables[variable].strip())
        flat.set("stroke", variables.get("cb", "none").strip())
        flat.set("stroke-width", "1")
        static.append(flat)
    return animated, ET.tostring(static, encoding="unicode") + "\n"


def bootstrap_svg(profile: dict, theme: str) -> str:
    """Create an honest initial card, never a fabricated contribution history."""
    tokens = theme_tokens(profile, theme)
    title = "GitHub contribution calendar awaiting first trusted refresh"
    description = "No contribution data is shown. GitHub Actions will generate this calendar after the first successful authenticated run."
    return "\n".join([
        '<svg xmlns="http://www.w3.org/2000/svg" width="880" height="192" viewBox="0 0 880 192" role="img" aria-labelledby="title desc">',
        f'<title id="title">{title}</title>',
        f'<desc id="desc">{description}</desc>',
        f'<rect x="1" y="1" width="878" height="190" rx="18" fill="{tokens["bg"]}" stroke="{tokens["border"]}" stroke-width="2"/>',
        f'<path d="M70 132H810" fill="none" stroke="{tokens["border"]}" stroke-width="2"/>',
        f'<circle cx="112" cy="94" r="26" fill="{tokens["surface"]}" stroke="{tokens["accent"]}" stroke-width="2"/>',
        f'<path d="M101 94H123M112 83V105" fill="none" stroke="{tokens["accent"]}" stroke-width="3" stroke-linecap="round"/>',
        f'<text x="164" y="79" font-family="Arial, Helvetica, sans-serif" font-size="25" font-weight="700" fill="{tokens["fg"]}">Contribution calendar awaiting first refresh</text>',
        f'<text x="164" y="111" font-family="Arial, Helvetica, sans-serif" font-size="19" fill="{tokens["muted"]}">GitHub Actions will replace this notice with a real contribution calendar.</text>',
        f'<text x="70" y="166" font-family="Arial, Helvetica, sans-serif" font-size="17" fill="{tokens["muted"]}">Run “Refresh profile artwork” after publishing; reduced motion will then use a static calendar.</text>',
        '</svg>',
        '',
    ])


def write_pair(folder: Path, theme: str, animated: str, static: str) -> None:
    staged = []
    for name, content in ((f"snake-{theme}.svg", animated), (f"contributions-{theme}.svg", static)):
        final = folder / name
        temporary = folder / f".{name}.tmp"
        temporary.write_text(content, encoding="utf-8")
        staged.append((temporary, final))
    for temporary, final in staged:
        temporary.replace(final)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare animated and static GitHub contribution calendars.")
    parser.add_argument("--bootstrap", action="store_true", help="write transparent initial placeholders without contribution data")
    args = parser.parse_args()
    profile = load_profile(ROOT)
    folder = ROOT / "assets" / "generated"
    folder.mkdir(parents=True, exist_ok=True)
    if args.bootstrap:
        for theme in ("light", "dark"):
            asset = bootstrap_svg(profile, theme)
            write_pair(folder, theme, asset, asset)
        print("Wrote honest contribution-calendar setup notices; no contribution data was invented")
        return
    brand = profile["identity"]["brand"]
    outputs: dict[str, tuple[str, str]] = {}
    for theme in ("light", "dark"):
        source = (folder / f"snake-{theme}.svg").read_text(encoding="utf-8")
        outputs[theme] = prepare(source, today(), brand)
    for theme, (animated, static) in outputs.items():
        write_pair(folder, theme, animated, static)
    print("Prepared accessible animated and reduced-motion contribution calendars")


if __name__ == "__main__":
    main()
