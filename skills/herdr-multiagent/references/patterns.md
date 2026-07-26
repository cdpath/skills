# Multi-agent patterns for Herdr

Reference for the fleet skill. Shapes verified against `herdr` 0.7.5. Commands print JSON on stdout; errors print JSON on stderr and exit 1 (server error) or 2 (CLI syntax).

## Contents

- [Verified result shapes](#verified-result-shapes)
- [Parallel fan-out (worktree per agent)](#parallel-fan-out-worktree-per-agent)
- [Shared-cwd sibling fan-out](#shared-cwd-sibling-fan-out)
- [One-shot agents](#one-shot-agents)
- [Dependency sequencing and fan-in](#dependency-sequencing-and-fan-in)
- [Handling `blocked`](#handling-blocked)
- [Result exchange via files](#result-exchange-via-files)
- [Error recovery](#error-recovery)
- [Per-agent-kind launch args](#per-agent-kind-launch-args)

## Verified result shapes

Parse IDs with `jq`.

```
worktree create   type: worktree_created
  .result.workspace.workspace_id            # -> worktree remove --workspace
  .result.tab.tab_id
  .result.root_pane.pane_id                  # -> agent start --pane
  .result.workspace.worktree.{checkout_path,repo_root,repo_name}
  .result.worktree.{branch,path,open_workspace_id}

worktree list      .result.worktrees[].{branch,path,open_workspace_id,is_prunable}
worktree remove    type: worktree_removed   .result.{workspace_id,path,forced}

workspace create   .result.workspace  .result.tab  .result.root_pane.pane_id
workspace close    .result.type == "ok"
tab create         .result.tab  .result.root_pane.pane_id
pane split         .result.pane.pane_id

agent start        type: agent_started
  .result.agent.{name,agent,pane_id,agent_status,interactive_ready,cwd,tab_id,workspace_id}
agent prompt       type: agent_prompted   .result.agent.{...}
agent wait                                 .result.agent.{...}
agent list         type: agent_list        .result.agents[].{name,pane_id,agent_status,cwd,tab_id}
agent get          type: agent_info        .result.agent.{...}
agent read         CLI prints text; socket API .result.read.text
```

States: `idle` (ready + tab seen), `working`, `blocked` (approval/question UI), `done` (idle after unseen background work), `unknown` (present, unclassified - not proof of completion).

## Parallel fan-out (worktree per agent)

Start every worker, submit every prompt, then wait on each. Wall time tracks the slowest worker, since `agent wait` returns at once for workers already settled.

```bash
#!/usr/bin/env bash
set -euo pipefail
REPO="${REPO:-$PWD}"          # a git repo
BASE="${BASE:-HEAD}"
OUT=/tmp/fleet; mkdir -p "$OUT"
before=$(herdr workspace list | jq -r '.result.workspaces[].workspace_id' | sort)

# workers: "name|kind|task"
workers=(
  "impl-a|codex|Implement feature A in src/a.rs. Write a summary to $OUT/impl-a.md and stop."
  "impl-b|codex|Implement feature B in src/b.rs. Write a summary to $OUT/impl-b.md and stop."
)

declare -A WID PANE
# 1. create isolated worktrees + start agents
for w in "${workers[@]}"; do
  IFS='|' read -r name kind task <<<"$w"
  wt=$(herdr worktree create --cwd "$REPO" --branch "$name" --base "$BASE" --no-focus --json)
  PANE["$name"]=$(printf '%s' "$wt" | jq -r '.result.root_pane.pane_id')
  WID["$name"]=$(printf  '%s' "$wt" | jq -r '.result.workspace.workspace_id')
  herdr agent start "$name" --kind "$kind" --pane "${PANE[$name]}" -- -a never -s workspace-write
done

# 2. submit all prompts (no --wait -> returns after submission)
for w in "${workers[@]}"; do
  IFS='|' read -r name kind task <<<"$w"
  herdr agent prompt "$name" "$task" --timeout 5000 >/dev/null
done

# 3. wait for each to settle (idle/done/blocked by default)
for w in "${workers[@]}"; do
  IFS='|' read -r name _ _ <<<"$w"
  herdr agent wait "$name" --timeout 300000 >/dev/null
done

# 4. collect results from files
for w in "${workers[@]}"; do
  IFS='|' read -r name _ _ <<<"$w"
  echo "=== $name ==="; cat "$OUT/$name.md" 2>/dev/null || echo "(no result file)"
done

# 5. teardown: remove worktrees, close any workspace this run added
for name in "${!WID[@]}"; do herdr worktree remove --workspace "${WID[$name]}" --force >/dev/null; done
after=$(herdr workspace list | jq -r '.result.workspaces[].workspace_id' | sort)
for id in $(comm -13 <(printf '%s\n' "$before") <(printf '%s\n' "$after")); do
  herdr workspace close "$id" >/dev/null
done
```

- `--timeout 5000` on `agent prompt` fails fast on a pane that is not accepting input; the 5 s stall guard applies only to `--wait`.
- For concurrent blocking, background the waits (`herdr agent wait "$name" --timeout 300000 &` then `wait`). Sequential waits over an already-prompted fleet are usually enough.
- `worktree remove` keeps each worker's branch; merge them later with `git`.

## Shared-cwd sibling fan-out

For workers that only read/analyze and cannot collide on writes - sibling panes in the current tab, no worktrees.

```bash
declare -A PANE
for w in "${workers[@]}"; do
  IFS='|' read -r name kind task <<<"$w"
  split=$(herdr pane split --current --direction right --cwd "$PWD" --no-focus)
  PANE["$name"]=$(printf '%s' "$split" | jq -r '.result.pane.pane_id')
  herdr agent start "$name" --kind "$kind" --pane "${PANE[$name]}"
done
for w in "${workers[@]}"; do IFS='|' read -r name _ task <<<"$w"; herdr agent prompt "$name" "$task" --timeout 5000 >/dev/null; done
for w in "${workers[@]}"; do IFS='|' read -r name _ _ <<<"$w"; herdr agent wait "$name" --timeout 300000 >/dev/null; done
```

Alternate `right`/`down` or split within fresh tabs (`herdr tab create`) to keep panes usable; repeated same-direction splits go unusably narrow.

## One-shot agents

Some agents run one task per invocation and exit - `oz agent run`, `codex exec`, `claude -p`, `gemini -p`. They are not persistent TUIs, so `agent start` / `agent prompt` / `agent wait` do not apply, and they do not appear in `agent list` or get lifecycle state. Dispatch each as a pane command and wait for a sentinel you print on completion:

```bash
# per one-shot worker (a worktree pane from the fan-out, or a sibling pane)
herdr pane run "$pane" "oz agent run --prompt '$esc'; echo __DONE__\$?"
herdr pane wait-output "$pane" --match "__DONE__" --timeout 300000
```

- The sentinel (`__DONE__<exit>`) prints when the agent exits; `pane wait-output` matches it in the recent snapshot. Read the exit code from the matched line.
- Collect results from files as usual - tell the worker to write its result to a path before exiting.
- Isolation is unchanged: still use worktree-per-agent if one-shot workers write the same repo concurrently.
- `oz` is one-shot and not a herdr `--kind`, so drive it only through panes. A `herdr.oz` launcher plugin can dispatch it from the focused pane's selected text.

## Dependency sequencing and fan-in

Wait for an upstream worker to settle before prompting a downstream one. Pass upstream output as a file path.

```bash
herdr agent prompt planner "Write an implementation plan to $OUT/plan.md, then stop." --wait --timeout 300000
for name in impl-a impl-b; do
  herdr agent prompt "$name" "Follow $OUT/plan.md for your part. Write results to $OUT/$name.md and stop." --timeout 5000 >/dev/null
done
for name in impl-a impl-b; do herdr agent wait "$name" --timeout 300000 >/dev/null; done
```

Fan in by running a final `merger` worker after all implementers settle, pointing it at every implementer's result file.

## Handling `blocked`

`blocked` means Herdr saw an approval or question UI. Read, then act:

```bash
herdr agent wait  "$name" --until blocked --timeout 300000
herdr agent read  "$name" --source recent-unwrapped --lines 80
herdr agent send-keys "$name" esc          # dismiss a prompt
herdr agent send-keys "$name" ctrl+c       # cancel the turn
herdr agent prompt "$name" "<revised instruction>" --wait --timeout 300000
```

Prefer launching workers with non-interactive flags (below) so they stay non-interactive. For a worker that must stay interactive, poll `agent list` and route each `blocked` worker to `send-keys` or a revised prompt.

## Result exchange via files

- Tell each worker: "Write your result to `<path>` as Markdown, reply with only the path, then stop."
- The driver reads the files. To chain, give a downstream worker the upstream file path in its task.
- Keep a per-worker directory (`/tmp/fleet/<name>/`) for multi-file results.

Reserve `agent read` for status checks and short confirmations.

## Error recovery

- **`agent_prompt_stalled`** (`--wait` only): the worker did not leave its start state within 5 s - it exited or sits at a login/update/trust screen. `herdr pane read <pane> --source recent-unwrapped --lines 60`, fix it (re-login, restart, accept trust), then re-prompt.
- **`agent_not_found`** for a name you started: the worker exited (crash, self-update, replaced). Re-check `herdr agent list`; if the pane is back at a shell prompt, `herdr agent start` the same name there again.
- **Alternate-screen reads** (Claude Code, OpenCode): `agent read --lines N` returns no more of a long response as N grows. Ask the worker to write its full response to a file and read the file.
- **`timeout`**: check `agent get`; if `working`, extend `--timeout` and wait again; if `blocked`/`unknown`, read and intervene.
- Wedged worker: `herdr agent send-keys <name> ctrl+c` to cancel the turn, then re-prompt or restart.

## Per-agent-kind launch args

Pass each agent's own non-interactive/approval flags after `--` so workers stay non-interactive. Verify exact flags with `<kind> --help`; the binary is authoritative.

- **codex** (verified): `-- -a never -s workspace-write` - no approval prompts; sandbox may write the working directory. Requires prior `codex login --device-auth`. On first launch after an upgrade codex self-updates and exits ("Please restart Codex"); `agent start` then reports the agent gone - start it again on the updated binary.
- **claude** (Claude Code): may enter `blocked` on permission prompts. Pass its non-interactive/permission flags after `--`, pre-approve the workspace, or handle `blocked` with `send-keys`. Confirm current flags with `claude --help`.
- **amp, gemini, others**: each has its own headless/approval mode. Check `<kind> --help` and pass flags after `--`. Otherwise expect `blocked` on approvals and handle it above.

Supported kinds: `pi`, `claude`, `codex`, `gemini`, `cursor`, `devin`, `agy`, `cline`, `omp`, `mastracode`, `opencode`, `copilot`, `kimi`, `kiro`, `droid`, `amp`, `grok`, `hermes`, `kilo`, `qodercli`, `maki`. Run `herdr agent` to confirm the installed list.
