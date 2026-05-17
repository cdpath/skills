---
name: homework-cli
description: Fetches and analyzes student homework from the welife001 parent-side API using the `homework` CLI. Use when the user asks about today's/recent/specific-date assignments, wants attachments interpreted by a VLM, or mentions homework, notice, 作业, 通知.
---

# Fetching Homework

The `homework` CLI reads homework notices for a single welife001 member and prints normalized JSON to stdout. It also stages attachments locally and, when a VLM is configured, returns a structured per-media analysis.

## Installation

```bash
go install github.com/cdpath/homework-cli/cmd/homework@latest
```

This drops the `homework` binary into `$(go env GOPATH)/bin` (commonly `~/go/bin`); make sure that directory is on `$PATH`. To build from a local checkout instead: `go build -o homework ./cmd/homework` inside the repo.

Verify: `homework cache path` should print the local cache root and exit 0.

## Configuration

Required values:

- `imprint` — long-lived bearer secret from the welife001 Mini Program. The CLI does **not** refresh it; on `imprint_invalid` the user must re-capture it manually.
- `member_id` — the student account id.
- `base_url` — defaults to `https://b.welife001.com`.

Three sources, precedence **flag > env > file**:

| | Imprint | Member | Base URL |
|---|---|---|---|
| flag | `--imprint` | `--member-id` | `--base-url` |
| env | `WELIFE_IMPRINT` | `WELIFE_MEMBER_ID` | `WELIFE_BASE_URL` |
| file | `imprint` | `member_id` | `base_url` |

Config file lives at `$XDG_CONFIG_HOME/homework-cli/config.json` (fallback `~/.config/homework-cli/config.json`):

```json
{
  "imprint": "<your-imprint>",
  "member_id": "<your-member-id>",
  "base_url": "https://b.welife001.com",
  "vlm": {
    "base_url": "https://your-openai-compatible-host/path",
    "model": "your-vision-model-id",
    "api_key": "<your-api-key>",
    "timeout_seconds": 60,
    "max_media_bytes": 20971520
  }
}
```

The `vlm` block is optional. Without it, media is still downloaded locally but `analysis.status` will be `unconfigured`. Any OpenAI-compatible multimodal endpoint works; the CLI POSTs to `<base_url>/v1/chat/completions` with images/video as base64 `data:` URLs. `api_key` is optional — when absent, no `Authorization` header is sent.

VLM env equivalents: `VLM_BASE_URL`, `VLM_MODEL`, `VLM_API_KEY`, `VLM_TIMEOUT_SECONDS`, `VLM_MAX_MEDIA_BYTES`.

If only the user knows their credentials, prompt them to drop their values into `~/.config/homework-cli/config.json` rather than passing the imprint on the command line. **Never echo, log, or commit the imprint or API key.**

## Quick commands

```bash
# Today's notices (list shape, no media analysis)
homework today

# Today's notices with detail + media analysis (top --limit 10 by default)
homework today --detail

# A specific date (yyyy-MM-dd, local TZ)
homework on 2026-05-15 --detail

# Server-tagged "recent" set
homework recent --detail

# Paginated history
homework history --page 0 --size 20

# One notice by id
homework show <notice_id>

# Inspect the embedded VLM prompt
homework prompt list
homework prompt show homework-media-v1

# Local-state inspection
homework cache path
homework cache stats
homework cache clear --analysis     # or --response, --media-store; no flag = all
```

Low-level pass-throughs (no normalization, no media): `homework api list`, `homework api detail <id>`.

## Key flags

- `--raw` — emit upstream JSON unchanged (no media pipeline).
- `--detail` — list verbs fan out to per-notice detail requests. Required to populate `media[]` and trigger analysis.
- `--limit N` — cap detail fan-out (default 10).
- `--skip-media` — bypass the whole media pipeline (no download, no VLM, no `analysis` object).
- `--no-cache` — disable response & analysis cache for this call (media store still used).
- `--refresh` — bypass response & analysis cache *reads*, then write fresh entries.
- `--vlm-base-url`, `--vlm-model`, `--vlm-api-key`, `--vlm-timeout-seconds`, `--vlm-max-media-bytes` — VLM overrides; only on `show` and list verbs.
- `--debug` — write JSONL diagnostics under `$XDG_CACHE_HOME/homework-cli/logs/`.

## Output shape

Normalized notice (truncated):

```json
{
  "id": "...", "class_id": "...", "create_at": "...",
  "title": "...", "subject": "...", "text_content": "...",
  "media": [
    {
      "kind": "image|video|audio|file",
      "url": "https://...",
      "name": "图片_1",
      "cache_path": "/Users/.../cache/media/<member_id>/<sha>.jpg",
      "analysis": {
        "status": "ok|cached|unconfigured|media_unavailable|model_error|unsupported",
        "media_summary": "...",
        "homework_interpretation": "...",
        "materials": [...],
        "warnings": [...],
        "error": null,
        "metadata": { "prompt_id": "...", "prompt_sha256": "...", "model": "...", ... }
      }
    }
  ]
}
```

`analysis.status` semantics:

- `ok` — fresh VLM call succeeded.
- `cached` — analysis cache hit (cheap, no VLM call).
- `unconfigured` — media stored locally but `vlm.base_url`/`vlm.model` missing.
- `unsupported` — file is not image/video by extension, or oversized (`error.code: "media_too_large"`), or provider rejected the input.
- `media_unavailable` — could not download the file.
- `model_error` — VLM call failed (`vlm_timeout` / `vlm_http_error` / `vlm_network`).

Partial success is normal: one notice can mix `ok`, `cached`, `unsupported` entries. The command exits 0 unless the underlying homework fetch itself fails.

## Recommended workflow

1. Start with a cheap text scan: `homework today --skip-media` (or `recent` / `on <date>`).
2. For notices that need attachments interpreted: re-run with `--detail` (list) or `show <id>` so the pipeline runs.
3. When summarizing to the user, lead with `text_content`, then per-media bullets using `analysis.homework_interpretation`. Surface `warnings` and any non-`ok`/`cached` statuses honestly.
4. Avoid `--refresh` unless the cached interpretation is clearly stale; cache hits are ~25 ms vs ~15 s for a fresh VLM call.
5. Never expose raw `--raw` output or the imprint to the user.

## Error codes

Stderr-JSON + non-zero exit on hard failures: `imprint_invalid` (3), `not_found` (4), `upstream_error` (5), `http_5xx` (6), `network` (7), `bad_request` (2). `cache_error` is a non-fatal stderr warning.
