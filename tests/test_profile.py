import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

from scripts import generate_activity as generator
from scripts.artwork import activity, load_profile
from scripts.generate_activity import public_repositories, render_files, summarize, unavailable_snapshot, write_all
from scripts.prepare_snake import NS, bootstrap_svg, prepare
from scripts.validate_profile import validate


def repository(identifier, **changes):
    row = {
        "id": identifier,
        "name": f"repo-{identifier}",
        "private": False,
        "fork": False,
        "owner": {"login": "malikskills"},
        "language": "Python",
    }
    row.update(changes)
    return row


class ActivityDataTests(unittest.TestCase):
    def test_filters_private_fork_and_other_owner_repositories(self):
        rows = [
            repository(1), repository(2, private=True), repository(3, fork=True),
            repository(4, owner={"login": "another-account"}),
        ]
        self.assertEqual(
            public_repositories("malikskills", lambda _: rows),
            [{"name": "repo-1", "language": "Python"}],
        )

    def test_follows_pages_and_deduplicates_by_stable_repository_id(self):
        pages = [[repository(index) for index in range(100)], [repository(99), repository(100)]]
        calls = []

        def fetch(path):
            calls.append(path)
            return pages[len(calls) - 1]

        result = public_repositories("malikskills", fetch)
        self.assertEqual(len(result), 101)
        self.assertIn("page=2", calls[1])

    def test_summary_treats_unclassified_as_a_bucket_not_a_language(self):
        snapshot = summarize(
            [{"language": "Python"}, {"language": "Python"}, {"language": None}],
            "malikskills", "2026-11-11",
        )
        self.assertEqual(snapshot["repositories"], 3)
        self.assertEqual(snapshot["primary_languages"], 1)
        self.assertEqual(snapshot["language_counts"], {"Python": 2, "Not classified": 1})

    def test_api_failure_is_not_converted_to_zero_statistics(self):
        with self.assertRaises(RuntimeError):
            public_repositories("malikskills", lambda _: (_ for _ in ()).throw(RuntimeError("offline")))

    def test_invalid_username_is_rejected_before_network_access(self):
        with self.assertRaises(ValueError):
            public_repositories("-bad", lambda _: self.fail("fetch must not be called"))

    def test_rendered_success_assets_share_one_snapshot_and_escape_xml(self):
        snapshot = summarize([{"language": "A&B"}], "malikskills", "2026-11-11")
        profile = load_profile()
        rendered = render_files(snapshot, profile)
        for theme in ("light", "dark"):
            for mobile in (False, True):
                name = f"activity-{'mobile-' if mobile else ''}{theme}.svg"
                root = ET.fromstring(rendered[name])
                self.assertEqual(root.get("width"), "480" if mobile else "1200")
                self.assertIn("2026-11-11", rendered[name])
                self.assertIn("A&amp;B", rendered[name])

    def test_unavailable_state_has_no_counts_and_renders_valid_svg(self):
        snapshot = unavailable_snapshot("malikskills", "Network unavailable during local bootstrap")
        self.assertNotIn("repositories", snapshot)
        self.assertIn("No verified statistics", activity(snapshot, False, False))
        ET.fromstring(activity(snapshot, True, True))

    def test_write_all_produces_complete_snapshot_set(self):
        profile = load_profile()
        snapshot = summarize([], "malikskills", "2026-11-11")
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "generated"
            write_all(render_files(snapshot, profile), output)
            saved = json.loads((output / "activity.json").read_text())
            self.assertEqual(saved["repositories"], 0)
            for theme in ("light", "dark"):
                self.assertTrue((output / f"activity-{theme}.svg").is_file())
                self.assertTrue((output / f"activity-mobile-{theme}.svg").is_file())

    def test_generate_commits_only_after_all_data_is_available(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "profile.json").write_text(json.dumps({
                "identity": {"github_username": "malikskills"},
                "colors": load_profile()["colors"],
                "illustrations": load_profile()["illustrations"],
            }))
            output = root / "assets/generated"
            with patch.object(generator, "ROOT", root), patch.object(generator, "OUTPUT", output), patch.object(
                generator, "load_profile", return_value=load_profile()
            ), patch.object(generator, "public_repositories", side_effect=RuntimeError("offline")):
                with self.assertRaises(RuntimeError):
                    generator.generate()
            self.assertFalse(output.exists(), "A failed fetch must not create an empty replacement snapshot")


class SnakePreparationTests(unittest.TestCase):
    def test_static_calendar_keeps_cells_without_animation(self):
        cells = '<rect class="c c0" x="2" y="2"/>' + '<rect class="c"/>' * 364
        source = (
            f'<svg xmlns="{NS}" viewBox="0 0 880 192"><style>'
            ':root{--ce:#112233;--cb:#000000;--c1:#45C47A}'
            '.c.c0{fill:var(--c1);animation-name:c0}</style>'
            f'{cells}<rect class="s"/><rect class="u"/></svg>'
        )
        animated, static = prepare(source, "2026-11-11")
        root = ET.fromstring(static)
        rectangles = root.findall(f"{{{NS}}}rect")
        self.assertEqual(len(rectangles), 365)
        self.assertEqual(rectangles[0].get("fill"), "#45C47A")
        self.assertNotIn("animation", static)
        self.assertIn("prefers-reduced-motion", animated)
        self.assertIn("MALIK DEV GitHub contribution calendar", static)

    def test_unknown_snake_markup_is_rejected(self):
        with self.assertRaises(ValueError):
            prepare(f'<svg xmlns="{NS}"/>', "2026-11-11")

    def test_bootstrap_calendar_is_explicitly_non_statistical(self):
        source = bootstrap_svg(load_profile(), "light")
        self.assertIn("real contribution calendar", source)
        self.assertNotIn("@keyframes", source)
        ET.fromstring(source)


class FullProjectValidationTests(unittest.TestCase):
    def test_repository_passes_its_offline_validator(self):
        svg_count, picture_sources = validate()
        self.assertEqual(svg_count, 28)
        self.assertEqual(picture_sources, 24)


if __name__ == "__main__":
    unittest.main()
