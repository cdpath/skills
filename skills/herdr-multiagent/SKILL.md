---
name: herdr-multiagent
description: Drive a fleet of coding agents through Herdr. Use when the user wants two or more agents running at once - parallel implementation in separate worktrees, or review-then-implement chains. Reaches the base `herdr` skill for single-agent primitives.
---

# Drive a fleet of agents through Herdr

A **fleet** is one **driver** agent (this one) coordinating many **worker** agents through the Herdr CLI. The driver provisions workers, dispatches work, waits for the fleet to **settle**, collects results, and tears down. Reaches the base `herdr` skill for `agent start`, `agent prompt --wait`, `agent wait`, `agent read`, and the `idle / working / blocked / done / unknown` states.

A fleet provisions the topology it needs - multiple workspaces, one worktree per writing worker. Preserve the driver's focus with `--no-focus` on every creation; close only workspaces you created (diff against the step-2 snapshot).

## Steps

**1. Confirm the driver is inside Herdr.**

```bash
test "${HERDR_ENV:-}" = 1
```

Done when the check passes. If it fails, say so and stop.

**2. Snapshot existing workspaces.**

```bash
before=$(herdr workspace list | jq -r '.result.workspaces[].workspace_id' | sort)
```

Done when `before` holds every pre-run workspace ID. Teardown closes only what this run added.

**3. Assign each worker an isolation topology.**

Match isolation to whether workers write the same files:

- read / analyze / review only -> **sibling panes**, shared cwd (`pane split`)
- write the same repo concurrently -> **worktree per agent** (`worktree create`, own branch)
- different repos / cwds -> **separate workspaces** (`workspace create`)

Done when every worker has one topology. Default writing workers to worktree-per-agent so concurrent edits never collide.

**Pane layout (sibling panes).** Default fleet layout: the **driver on the left (full height)**, workers **stacked in a column on the right** - `main | work1 / work2 / work3`. Build it with one vertical split (`--direction right`) off the driver for the worker group, then horizontal splits (`--direction down`) to stack the workers. This keeps the driver readable; naively repeating `--direction right` instead shrinks the driver and gives reversed, narrow columns. The user can override - all side-by-side columns, all stacked, one worker per tab (`tab create`), or a separate workspace / new window. Full recipe + `--ratio` sizing in `references/patterns.md`.

**4. Provision, start, and prompt each worker.**

```bash
wt=$(herdr worktree create --cwd "$REPO" --branch "$BRANCH" --no-focus --json)
pane=$(printf '%s' "$wt" | jq -r '.result.root_pane.pane_id')
wid=$(printf '%s'  "$wt" | jq -r '.result.workspace.workspace_id')
herdr agent start "$NAME" --kind codex --pane "$pane" -- -a never -s workspace-write
herdr agent prompt "$NAME" "$TASK" --timeout 5000 >/dev/null
```

Done when every worker is started and prompted. Prompt without `--wait` so the fleet runs in parallel; record each worker's `$wid` and `$pane`.

`agent` targets accept the `$NAME` registered by `agent start` or a pane id hosting an agent. For agents you did not start (no registered name; `agent list` shows none), the pane id is the only valid target - the agent label (`droid`, `pi`) is not.

**5. Wait for the fleet to settle.**

```bash
for name in "${!PANE[@]}"; do herdr agent wait "$name" --timeout 300000; done
```

Done when every worker has settled to `idle`, `done`, or `blocked`. `agent wait` returns at once for workers already settled, so wall time tracks the slowest worker. Route any `blocked` worker per `references/patterns.md`.

**One-shot agents.** The steps above assume a persistent agent you start, prompt, and wait on. Some agents run one task per invocation and exit (`oz agent run`, `codex exec`, `claude -p`, `gemini -p`): skip `agent start` / `agent prompt` / `agent wait`, dispatch each as a pane command that writes its result and an `.exit` sentinel to files, then poll for the `.exit` file and read the result. They do not appear in `agent list` or get state tracking. See `references/patterns.md`.

**6. Collect results from files.**

Each worker writes its result to a known path (e.g. `/tmp/fleet/<name>.md`) and replies with the path; the driver reads the files. Done when every worker's result file is read. Files are the channel between agents - terminal reads are lossy for full-screen agents and racy across workers.

**7. Tear down.**

```bash
for wid in "${WID[@]}"; do herdr worktree remove --workspace "$wid" --force; done
after=$(herdr workspace list | jq -r '.result.workspaces[].workspace_id' | sort)
for id in $(comm -13 <(printf '%s\n' "$before") <(printf '%s\n' "$after")); do
  herdr workspace close "$id"
done
```

Done when every worktree is removed and the workspace list again matches `before`.

## Using Oz (Warp)

`oz agent run` is one-shot - one task per invocation, then it exits. Herdr does not recognize Oz as a native agent kind, so it never appears in `agent list` and gets no lifecycle state. Drive it two ways:

- **Interactive, on selected text.** Install the `herdr.oz` plugin (from [cdpath/herdr-oz](https://github.com/cdpath/herdr-oz)) - it splits a sibling pane and runs Oz on the focused pane's selection:

  ```bash
  herdr plugin install cdpath/herdr-oz
  herdr plugin action invoke herdr.oz.run --plugin herdr.oz        # herdr.oz.run-cloud for cloud runs
  ```

  Select the task text in a pane first - the selection is the prompt. Or bind `herdr.oz.run` to a key in `config.toml`. Knobs: `OZ_OUTPUT_FORMAT=text` for a cleaner pane, or `OZ_CAPTURE_DIR=/tmp/oz` to redirect `--output-format json` to a file (plus an `.exit` sentinel) for a driver to read.

- **As a fleet worker.** Oz is one-shot, so skip `agent start` / `agent prompt` / `agent wait`. Dispatch it as a pane command that writes `--output-format json` to a file plus an `.exit` sentinel, then poll for the `.exit` file and `jq`-parse the result. Recipe in `references/patterns.md` -> "One-shot agents".

## Reference

`references/patterns.md` holds the full runnable fan-out loop, verified JSON result shapes, the sibling-pane variant, one-shot agents (`oz agent run`, `codex exec`), dependency sequencing and fan-in, `blocked`-approval handling, error recovery (`agent_prompt_stalled`, `agent_not_found`, alternate-screen reads), and per-agent-kind launch args. Read it for anything beyond the spine above.
