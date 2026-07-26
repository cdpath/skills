#!/bin/sh
# herdr Oz plugin - dispatch a Warp Oz agent task in a sibling pane.
#
# Prompt source: the focused pane's selected text (HERDR_PLUGIN_CONTEXT_JSON).
# Invoke:  herdr plugin action invoke herdr.oz.run        --plugin herdr.oz
#          herdr plugin action invoke herdr.oz.run-cloud  --plugin herdr.oz
# Bind a key to the action in config.toml to run Oz on the selected text.
#
# Oz is one-shot (`oz agent run --prompt`), so each invocation runs one task in
# its own pane and returns to the shell prompt when done. Herdr does not detect
# Oz as a native agent kind, so this plugin launches and monitors via panes only.

set -eu

HERDR="${HERDR_BIN_PATH:-herdr}"
mode="${1:-run}"   # "run" -> oz agent run ; "cloud" -> oz agent run-cloud

# Parse the plugin context JSON for the selected-text prompt and the focused pane cwd.
prompt=""
cwd="$PWD"
if [ -n "${HERDR_PLUGIN_CONTEXT_JSON:-}" ] && command -v python3 >/dev/null 2>&1; then
  eval "$(printf '%s' "${HERDR_PLUGIN_CONTEXT_JSON}" | python3 -c '
import json, sys, shlex
d = {}
try:
    d = json.load(sys.stdin)
except Exception:
    pass
print("prompt=" + shlex.quote((d.get("selected_text") or "").strip()))
c = d.get("focused_pane_cwd") or ""
if c:
    print("cwd=" + shlex.quote(c))
')"
fi

if [ -z "$prompt" ]; then
  echo "herdr.oz.$mode: no prompt. Select the task text in a pane, then invoke this action." >&2
  exit 1
fi

# Split a sibling pane beside the focused one; preserve cwd; keep focus on the caller.
split="$("$HERDR" pane split --current --direction right --cwd "$cwd" --no-focus)" || {
  echo "herdr.oz.$mode: pane split failed" >&2
  exit 1
}
pane="$(printf '%s' "$split" | python3 -c 'import json,sys;print(json.load(sys.stdin)["result"]["pane"]["pane_id"])')"

# Single-quote-escape the prompt, then dispatch oz in the new pane.
esc="$(printf '%s' "$prompt" | sed "s/'/'\\\\''/g")"
if [ "$mode" = "cloud" ]; then
  oz_cmd="oz agent run-cloud --prompt '$esc'"
else
  oz_cmd="oz agent run --prompt '$esc'"
fi
"$HERDR" pane run "$pane" "$oz_cmd"

echo "oz dispatched in pane $pane ($mode)"
echo "$pane"
