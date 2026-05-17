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

## Layout

```
.
├── .claude-plugin/
│   └── plugin.json          # declares skill paths for the installer
└── skills/
    └── <skill-name>/
        └── SKILL.md         # frontmatter: name + description, then body
```

To add a new skill: create `skills/<name>/SKILL.md` with `name` + `description` frontmatter, then list its path in [`.claude-plugin/plugin.json`](./.claude-plugin/plugin.json).
