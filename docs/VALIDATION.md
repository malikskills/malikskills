# Installation, generation and validation

## Local environment

The generators use Python's standard library. A virtual environment is optional but recommended for installing the optional pytest runner without changing global packages:

```sh
cd ~/Projects/GitHub-Research/malik_dev-profile
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## Build the profile artwork

```sh
python3 scripts/build_editorial_assets.py
```

This command regenerates the banner, logo, engineering map, project cards, technology landscape and approach SVGs. It does not access GitHub or alter activity data.

## Generate verified GitHub activity

Run this only with access to the GitHub REST API. An optional `GH_TOKEN`/`GITHUB_TOKEN` improves rate limits but is not stored.

```sh
GH_TOKEN="$(gh auth token)" python3 scripts/generate_activity.py
```

The command produces `activity.json`, `activity.md` and light/dark desktop/mobile dashboard assets. It fails instead of emitting zeros or guessing data. If the account has not yet yielded a successful fetch, use the transparent setup state only during initial local creation:

```sh
python3 scripts/generate_activity.py --bootstrap-unavailable "Initial local build has no GitHub API access"
python3 scripts/prepare_snake.py --bootstrap
```

After publishing, use the **Refresh profile artwork** workflow to replace both setup states with real GitHub data and a real contribution calendar.

## Test and validate

```sh
python3 -m unittest discover -s tests -v
python3 scripts/validate_profile.py
```

When pytest is installed, its collection is also supported:

```sh
python -m pytest -q
```

The validator checks JSON shape and identity, contact honesty, project verification states, README sections and local links, all theme/mobile matrix files, SVG XML/safety/accessibility rules, activity arithmetic, static calendar motion rules and pinned Action references. It is more than an exit-code check: it parses each SVG and verifies actual generated content.

Optional checks when the tools are installed:

```sh
actionlint
markdownlint README.md docs/*.md assets/generated/activity.md
git diff --check
```

## Hosted first run checklist

1. Create the remote profile repository named exactly `workcmtiayon-arch` and push only when you choose to publish.
2. In **Settings → Actions → General**, permit `GITHUB_TOKEN` write access only if you intend to authorize generated-art commits.
3. Run **Refresh profile artwork** manually with `publish: false` first and inspect the artifact.
4. Once the artifact is satisfactory, run it again with `publish: true`; alternatively set the `PROFILE_AUTO_COMMIT` Actions variable to `true` to authorize future scheduled commits.
5. Confirm the snake action and activity fetch succeeded, then visually review the hosted profile in light, dark, mobile and reduced-motion modes.

No personal access token, password or email address is required by this repository. The GitHub Actions `github.token` is sufficient for the public API and contribution generator. Branch protection may require a maintainer-approved update path for the optional generated-art commit.
