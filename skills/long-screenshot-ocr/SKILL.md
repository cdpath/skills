---
name: long-screenshot-ocr
description: |
  Use when the user uploads or references a long screenshot of a Feishu/Lark/web wiki page and asks to extract text, OCR, split and stitch, remove watermarks, or output Markdown. Trigger on phrases like "OCR this long screenshot", "split screenshot and OCR", "extract markdown from screenshot", "convert screenshot to markdown", or explicit mentions of overlap/deduplicate. Do not use for single short screenshots that fit in one vision call.
---

# Long-screenshot OCR

Extract a tall web/wiki screenshot into clean Markdown by splitting it into overlapping **chunks**, reading each chunk, **stitching** the text, and stripping UI **noise**.

## Steps

1. **Inspect the image.**
   - Read dimensions `(width, height)` and format with an available local image tool.
   - Prefer already-available tools: importable Python `PIL` first, then `ffmpeg`/`ffprobe`.
   - Do not run `pip install`, create a venv, or install persistent dependencies. If neither Pillow nor ffmpeg is available and slicing is still needed, use `uvx --with pillow python ...` for that one command only.
   - Completion criterion: you know exact width, height, and that the image is a vertical long screenshot.

2. **Create a temp directory.**
   - Run `mktemp -d /tmp/feishu_ocr.XXXXXX`.
   - Completion criterion: a unique `/tmp/feishu_ocr.<random>/` directory exists and its path is recorded.

3. **Split into overlapping chunks.**
   - Use [`scripts/split_long_screenshot.py`](scripts/split_long_screenshot.py) when available:
     `python3 <skill-dir>/scripts/split_long_screenshot.py <input-image> --out-dir <temp-dir>`.
   - The script uses importable Pillow if present, otherwise existing `ffmpeg`/`ffprobe`.
   - If the script reports that neither tool is available, run it once through `uvx --with pillow python <skill-dir>/scripts/split_long_screenshot.py ...`.
   - Slice vertically with `chunk_height = 2500 px` and `overlap = 500 px`.
   - Save as `chunk_{idx:03d}_{top}_{bottom}.png` so every filename encodes its pixel range.
   - Completion criterion: the full height is covered, the last chunk ends exactly at `height`, and every adjacent pair shares 500 px.

4. **Read every chunk.**
   - Use the current model's vision capability to transcribe each chunk, preserving headings, tables, lists, and fenced code blocks.
   - Do not install or run third-party OCR tools in the normal path. If the model can see images, reading the chunk images is the OCR step.
   - Use Tesseract or another OCR engine only when the user explicitly asks for full automation/no-vision OCR, or when model vision is unavailable. If needed, use an already-installed OCR engine first; install nothing without user approval.
   - Completion criterion: every chunk has a corresponding raw text excerpt.

5. **Stitch and deduplicate.**
   - Align adjacent chunks using their 500 px overlap.
   - Keep one copy of each duplicated paragraph; drop broken fragments that span the boundary.
   - Completion criterion: reading the stitched text from top to bottom flows naturally with no repeated adjacent paragraphs.

6. **Strip noise.**
   - Remove: page header, company/confidentiality banners, left sidebar, right-side AI/action buttons, bottom "你可能还想问" widget, "真诚点赞，手留余香" footer, and page-number watermarks.
   - Completion criterion: only the main document content remains.

7. **Format and save.**
   - Convert into Markdown with `#`/`##` headings, `|` tables, ` ``` ` code blocks, and `-`/`1.` lists.
   - Save the final Markdown next to the input image by replacing the input screenshot extension with `.md`.
   - Example: `screencapture-foo-2026-06-24.png` -> `screencapture-foo-2026-06-24.md`.
   - Do not rename the final file from the visible document title. A temp file may use an internal name such as `stitched.md`, but the delivered file should be derived from the input filename unless the user provided an explicit output path.
   - Completion criterion: the output file exists and renders correctly as Markdown.

## Reference

### Parameters

| Parameter | Value | Purpose |
| --- | --- | --- |
| `chunk_height` | 2500 px | Keeps each vision call manageable while preserving context. |
| `overlap` | 500 px | Gives a deduplication anchor between adjacent chunks. |
| OCR primary path | Vision | Handles mixed layout, tables, and code better than local OCR. |
| OCR fallback | Existing Tesseract only | Use only for explicit no-vision/full-automation requests. |

### Split formula

```python
top = 0
while top < height:
    bottom = min(top + chunk_height, height)
    crop = img.crop((0, top, width, bottom))
    crop.save(f"{out_dir}/chunk_{idx:03d}_{top}_{bottom}.png")
    if bottom == height:
        break
    top = bottom - overlap
```

### Tools

- Existing Python + Pillow or existing `ffmpeg`/`ffprobe` for slicing.
- `uvx --with pillow` for one-shot slicing only when no local image tool is available.
- Vision capability for the primary transcription path.
- Tesseract + language packs for fallback only when explicitly requested or vision is unavailable.

### Failure modes

- **Repeated paragraphs** — overlap was not used or deduplication was skipped; fix by re-checking the 500 px overlap.
- **Missing boundary text** — chunk height too large or overlap too small; verify chunks cover the full height and share overlap.
- **UI noise in output** — the strip-noise step was skipped; re-run step 6 against the full stitched text.
- **Garbled tables/code** — vision was bypassed for Tesseract on complex layouts; prefer vision for tables and code blocks.
- **Slow dependency setup** — local tools were not checked first; use existing Pillow or `ffmpeg`/`ffprobe`, and only then a one-shot `uvx --with pillow` command.
- **Wrong output filename** — the document title was used; rename final output from the input screenshot basename with `.md`.
