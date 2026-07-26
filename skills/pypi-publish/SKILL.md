---
name: pypi-publish
description: Publish a Python package to PyPI via GitHub Actions and Trusted Publishing (OIDC). Use when working with a release publish workflow (e.g. `python-publish.yml`), GitHub Releases, PyPI Trusted Publishing/OIDC, `pyproject.toml` package metadata, or version/tag bump helpers.
---

# Publish a Python package to PyPI

Reference for release-driven PyPI publishing through GitHub Actions with **Trusted Publishing** (OIDC) — no stored API tokens. The package is built from `pyproject.toml`, uploaded as a build artifact, and published when a **GitHub Release** is published.

## Core workflow: release-driven

Inspect the repo's publish workflow first (commonly `.github/workflows/python-publish.yml`). Publishing fires on a published **GitHub Release**, not on a pushed tag:

```yaml
on:
  release:
    types: [published]
```

A pushed tag alone does **not** publish to PyPI — a GitHub Release must be published for that tag. This is the single most common reason for "I pushed the tag but PyPI didn't update."

## Build job

The build job typically checks out the repo, sets up Python, installs `build`, runs `python -m build`, and uploads `dist/` as an artifact (e.g. `release-dists`).

`pyproject.toml` declares the build backend — Hatchling is a common choice:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

To validate locally without the workflow: `python -m pip install build && python -m build`, then inspect `dist/` for a `.whl` and a `.tar.gz`.

## Publish job

The publish job depends on the build job, downloads the `dist/` artifact, and publishes with the official action:

```yaml
uses: pypa/gh-action-pypi-publish@release/v1
with:
  packages-dir: dist/
```

Authentication is **Trusted Publishing** via GitHub OIDC. The essential bits:

```yaml
permissions:
  id-token: write        # required for OIDC
environment:
  name: pypi             # must match the trusted publisher configured on PyPI
```

`id-token: write` is the heart of Trusted Publishing: PyPI trusts the GitHub OIDC token instead of a stored API token. The PyPI project must be configured as a trusted publisher matching this repository, the workflow filename, and the environment name.

## Package metadata

Read `pyproject.toml` for the published identity. The distribution name, import package, and current version all live there — do not copy the version elsewhere; it changes every release.

```toml
[project]
name = "<distribution-name>"          # name on PyPI

[project.scripts]
<entry-point> = "<import_pkg>.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["<import_pkg>"]           # import name can differ from distribution name
```

## Version and release helper

A typical bump helper updates the version in `pyproject.toml`, commits, and creates an annotated tag:

```bash
./scripts/bumpversion.sh patch        # or minor / major
git push && git push --tags
```

Then publish a **GitHub Release** for the tag — that is what triggers the publish workflow.

## Failure modes

- **Tag pushed but PyPI not updated** — publishing is release-driven, not tag-driven; publish the GitHub Release for that tag.
- **Trusted Publishing permission / OIDC error** — the PyPI trusted publisher config doesn't match this repo, workflow filename, or environment name (e.g. `pypi`).
- **Build succeeded, publish found no files** — the publish job didn't download the build artifact into `dist/`; check the artifact name and `packages-dir`.
- **Wrong version published** — the version in `pyproject.toml` wasn't bumped before the release; the build reads it from there.
- **Local dist doesn't match CI** — different build backend or stale `dist/`; rebuild with `python -m build` from a clean checkout.

## Operating notes

- Require an explicit user request before pushing commits or tags.
- Keep this repository on Trusted Publishing; no PyPI API tokens in secrets.
- Before changing release automation, read `pyproject.toml`, the publish workflow, and the bump helper together.
