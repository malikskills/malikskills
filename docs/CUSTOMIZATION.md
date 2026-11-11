# Customization guide

`profile.json` is the authoritative source for the public identity, wording, projects, technology groups, colours and generator configuration. Edit it first, then rebuild the artwork; do not hand-edit generated SVGs.

## Identity and contacts

Update `identity.brand`, `identity.name`, `identity.location`, `identity.role`, `identity.positioning` and `identity.tagline` together. `identity.github_username`, `identity.github_url` and `contacts.github` must stay aligned. Email, LinkedIn and portfolio remain `null` until a real public URL is available; adding a guessed contact is deliberately rejected by the validator.

## Projects and technology claims

Each project has a `repository`, `repository_candidates` and `repository_verification` field. Leave `repository` as `null` and the verification state as `pending_public_verification` until the public URL has been checked. Once verified, set the exact HTTPS URL and change the state to `verified_public`, then add an honest link to the README.

The four technology groups intentionally distinguish practiced foundations, project-context tools, active learning and deeper study. This profile never uses percentage bars or inferred skill levels. Keep project targets and planned infrastructure in their dedicated fields so artwork and prose do not present them as deployed software.

## Colours and editorial assets

The light and dark colour systems are under `colors`. Every hexadecimal colour is checked by the validator. `scripts/artwork.py` reads these values and builds the hero, logo, legacy system map, project cards, stack map and six-step approach. Its output has four themed variants for every responsive component:

- desktop light and dark;
- mobile light and dark.

Rebuild only those editorial files with:

```sh
python3 scripts/build_editorial_assets.py
```

The layout uses 1200-unit desktop artboards and 480-unit mobile artboards. README `<picture>` sources switch at 760 px and use GitHub-supported `prefers-color-scheme` media queries. The README uses no JavaScript, remote font, arbitrary stylesheet or script.

## Live activity data

`scripts/generate_activity.py` reads public REST metadata from `https://api.github.com`. It counts only repositories owned by `malikskills`, excludes forks, includes archived originals and groups one GitHub primary language per repository. It does not calculate commits, total bytes, proficiency or completion status.

For an authenticated local refresh, create a token through `gh auth login` or provide a token through the shell only:

```sh
gh auth login
GH_TOKEN="$(gh auth token)" python3 scripts/generate_activity.py
```

The token is never written to `profile.json`, a file or a log. The generator renders every SVG in memory and writes temporary files before replacing its asset set. If the API fails, it exits non-zero and keeps the last successful files. The count-free bootstrap state used in this local delivery is truthful and can be replaced only by a successful API fetch:

```sh
python3 scripts/generate_activity.py --bootstrap-unavailable "Initial local build has no GitHub API access"
```

## Contribution snake and Actions

The refresh workflow invokes `Platane/snk/svg-only` with the standard GitHub Actions token and then runs `scripts/prepare_snake.py`. That script adds accessibility metadata to the animated SVG and derives a real static grid for `prefers-reduced-motion`. It rejects an unfamiliar upstream SVG format rather than publishing an empty fallback.

No secret is needed for a public profile: `github.token` has sufficient access to the public contribution calendar. A token may include anonymized private-contribution cells only if GitHub account settings expose them; it does not reveal private repository names. Never paste a personal access token in this repository.

Before the first hosted run, the checked-in snake files are intentionally informational placeholders, not fabricated contribution data. The workflow will replace them after it successfully obtains real GitHub data.

The `publish` job cannot commit generated files accidentally: manually dispatch **Refresh profile artwork** with `publish: true`, or explicitly create a repository Actions variable named `PROFILE_AUTO_COMMIT` with the value `true` to authorize scheduled commits. The job commits only `assets/generated/`; it does not deploy or publish a GitHub repository.
