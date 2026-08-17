# skills

My agent skills, installable via [skills.sh](https://skills.sh).

## Install

Install all skills:

```bash
npx skills@latest add cdpath/skills
```

Install a specific skill:

```bash
npx skills@latest add cdpath/skills --skill homework-cli
# or equivalently
npx skills@latest add cdpath/skills@homework-cli
```

The CLI auto-detects your coding agent (Claude Code, Cursor, Amp, etc.) and installs the skill(s) into the right directory.

## Skills

- **[homework-cli](./skills/homework-cli/SKILL.md)** — Fetches and analyzes student homework from the welife001 parent-side API using the `homework` CLI.
- **[anki-connect](./skills/anki-connect/SKILL.md)** — Uses AnkiConnect to inspect and automate Anki through the local HTTP API, with warnings for mutating and destructive actions.
- **[anki-vocab-cards](./skills/anki-vocab-cards/SKILL.md)** — Creates source-backed Anki vocabulary and phrase cards for working vocabulary.
- **[obsidian-category](./skills/obsidian-category/SKILL.md)** — Creates new categories in an Obsidian vault.
- **[tufte-viz](./skills/tufte-viz/SKILL.md)** — Ideate and critique data visualizations using Edward Tufte's principles. (via [gist](https://gist.github.com/aparente/e48c353755958621b3c0004593105a90))
- **[long-screenshot-ocr](./skills/long-screenshot-ocr/SKILL.md)** — Extracts long screenshots into clean Markdown using local slicing tools and model vision.
- **[pypi-publish](./skills/pypi-publish/SKILL.md)** — Publish a Python package to PyPI via GitHub Actions and Trusted Publishing (OIDC).
- **[herdr-multiagent](./skills/herdr-multiagent/SKILL.md)** — Drives a fleet of coding agents through Herdr: parallel implementation in separate worktrees, or review-then-implement chains. Requires the `herdr` CLI.
- **[no-ai-slop](./skills/no-ai-slop/SKILL.md)** — Edits drafts into sharper, more human writing while preserving the writer's personal voice, or detects AI-slop patterns without rewriting.
- **[spark](./skills/spark/SKILL.md)** — Collaborative brainstorming that walks a raw idea to a committed spec, then stops. Includes a hard gate that blocks coding until the design is approved.
- **[explain-diff-html](./skills/explain-diff-html/SKILL.md)** — Produces a rich, interactive single-file HTML explanation of a code change, diff, branch, or PR, with background, intuition, walkthrough, and a quiz. (via [gist](https://gist.github.com/geoffreylitt/a29df1b5f9865506e8952488eac3d524))
- **[demo-optimization](./skills/demo-optimization/SKILL.md)** — Optimizes product demos, prototype presentations, and hackathon pitches.

## Layout

```
.
├── .claude-plugin/
│   └── plugin.json          # declares skill paths for the installer
└── skills/
    └── <skill-name>/
        ├── SKILL.md         # frontmatter: name + description, then body
        ├── config.example.json   # optional
        └── scripts/         # optional bundled helpers
```

To add a new skill: create `skills/<name>/SKILL.md` with `name` + `description` frontmatter, then list its path in [`.claude-plugin/plugin.json`](./.claude-plugin/plugin.json).
