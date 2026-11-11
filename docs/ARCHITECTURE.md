# Architecture

## Boundaries and source of truth

The repository has no application runtime and no third-party Python package dependency. `profile.json` is the single public configuration source. `scripts/artwork.py` reads it to create all editorial SVGs; `scripts/generate_activity.py` reads it to identify the GitHub account; `scripts/validate_profile.py` checks it against the README and generated files.

```text
profile.json
 ├── artwork.py ────────────────> assets/branding/*.svg + assets/projects/*.svg
 ├── generate_activity.py ──────> assets/generated/activity.{json,md,svg}
 ├── prepare_snake.py ──────────> assets/generated/{snake,contributions}-*.svg
 └── validate_profile.py ───────> offline integrity report

README.md ── picture/source references ──> generated and editorial SVG variants
```

## Asset responsibilities

`assets/branding/` contains the hero, M monogram, small system map, stack landscape and engineering approach. `assets/projects/` contains one original, non-screenshot diagram per project. `assets/generated/` is reserved for API-derived activity snapshots and the contribution animation/static fallback. The refresh workflow is the only planned automatic writer of the generated directory after the project is hosted.

`build_editorial_assets.py` is a small executable entry point for the deterministic static generator. No activity request is made during editorial builds.

## Data and failure behavior

The activity generator pages through `GET /users/{username}/repos?type=owner&per_page=100`, deduplicates repositories by GitHub id and keeps only public, owned, non-fork repositories. GitHub's `language` field supplies exactly one primary language per repository. The generator writes all rendering output to temporary files before replacements. A failed request raises an error before any destination is modified.

The contribution workflow relies on `Platane/snk/svg-only` to query GitHub's contribution data via the Actions token. `prepare_snake.py` validates the expected 350–378-cell upstream grid, inserts accessible title/description metadata and flattens the initial cell levels into a separate non-animated SVG. An unknown format stops the workflow.

## Automation and authority

The workflows run on `main` and derive the GitHub account from the repository owner, so they remain valid after an account rename. The generation job has `contents: read`. A separate publish job gains `contents: write` only after a manual dispatch with `publish: true`, or after the owner explicitly enables the `PROFILE_AUTO_COMMIT=true` repository Actions variable. It stages only `assets/generated/`.

The source repository audited for the requested functional reference did not provide a licence file. This project therefore recreates the architecture, prose and artwork independently; it contains no copied reference SVG, Python source or generated data.
