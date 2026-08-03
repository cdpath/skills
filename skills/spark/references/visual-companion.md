# Visual Companion

A local web tool for presenting visual concepts — UI mockups, architecture diagrams, or side-by-side options. Switch to it when imagery aids comprehension; keep the terminal for text and tables (scoping, trade-off matrices).

## How it works

A background server watches a session `content/` directory. You write HTML snippets into it (for example `layout.html`), and the server surfaces the latest file. Viewer clicks are captured as structured JSON you can read back.

## Start the server

```bash
"$skill_dir/scripts/start-server.sh" --project-dir <repo-root>
```

Parse the JSON line it prints; it contains the `url` and the session directory.

Options:

- `--project-dir <path>` — persist session files under `<path>/.superpowers/brainstorm/`. Without it, files go to an ephemeral `/tmp/brainstorm-*` directory.
- `--host <bind-host>` — interface to bind (default `127.0.0.1`; use `0.0.0.0` in containers or remote environments).
- `--url-host <host>` — hostname shown in the returned URL.
- `--foreground` — run in the current terminal.
- `--background` — force background mode.

## Author a page

Write an HTML snippet into the session's `content/` directory:

```bash
<session-dir>/content/layout.html
```

The server serves the latest file. Use distinct filenames to switch pages. The renderer offers styled layouts for option lists, image cards, split comparisons, and rough UI elements (see `scripts/frame-template.html`).

Best practices:

- Limit the number of alternatives shown at once.
- Swap placeholder text for realistic copy where authenticity matters.
- Calibrate polish to the decision under review.

## Stop the server

```bash
"$skill_dir/scripts/stop-server.sh" <session-dir>
```

When the conversation returns to text-only, push a standby page so stale visuals clear before you stop.
