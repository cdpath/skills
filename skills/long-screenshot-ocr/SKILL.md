---
name: long-screenshot-ocr
description: |
  Use when the user uploads or references a long screenshot of a Feishu/Lark/web wiki page and asks to extract text, OCR, split and stitch, remove watermarks, or output Markdown. Trigger on phrases like "OCR this long screenshot", "split screenshot and OCR", "extract markdown from screenshot", "convert screenshot to markdown", or explicit mentions of overlap/deduplicate. Do not use for single short screenshots that fit in one vision call.
---

# Long-screenshot OCR

Extract a tall web/wiki screenshot into clean Markdown by splitting it into overlapping **chunks**, reading each chunk, **stitching** the text, and stripping UI **noise**.

## Steps

1. **Inspect the image.**
   - Read dimensions `(width, height)` and format.
   - Completion criterion: you know exact width, height, and that the image is a vertical long screenshot.

2. **Create a temp directory.**
   - Run `mktemp -d /tmp/feishu_ocr.XXXXXX`.
   - Completion criterion: a unique `/tmp/feishu_ocr.<random>/` directory exists and its path is recorded.

3. **Split into overlapping chunks.**
   - Slice vertically with `chunk_height = 2500 px` and `overlap = 500 px`.
   - Save as `chunk_{idx:03d}_{top}_{bottom}.png` so every filename encodes its pixel range.
   - Completion criterion: the full height is covered, the last chunk ends exactly at `height`, and every adjacent pair shares 500 px.

4. **Read every chunk.**
   - Use vision to transcribe each chunk, preserving headings, tables, lists, and fenced code blocks.
   - If the user explicitly requests full automation, fall back to Tesseract with `chi_sim+eng`, `--psm 6`, and pre-processing (grayscale + 1.5× contrast).
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
   - Save as `ocr_vision_stitched.md` or a name matching the task.
   - Completion criterion: the output file exists and renders correctly as Markdown.

## Reference

### Parameters

| Parameter | Value | Purpose |
| --- | --- | --- |
| `chunk_height` | 2500 px | Keeps each vision call manageable while preserving context. |
| `overlap` | 500 px | Gives a deduplication anchor between adjacent chunks. |
| Tesseract PSM | 6 | Assumes a single uniform block of text. |
| Tesseract languages | `chi_sim+eng` | Handles Chinese/English mixed content. |
| Contrast boost | 1.5× | Improves Tesseract accuracy on low-contrast screenshots. |

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

- Python + Pillow for slicing and pre-processing.
- Tesseract + tesseract-lang (chi_sim/eng) for the fallback path only.
- Vision capability for the primary transcription path.

### Failure modes

- **Repeated paragraphs** — overlap was not used or deduplication was skipped; fix by re-checking the 500 px overlap.
- **Missing boundary text** — chunk height too large or overlap too small; verify chunks cover the full height and share overlap.
- **UI noise in output** — the strip-noise step was skipped; re-run step 6 against the full stitched text.
- **Garbled tables/code** — vision was bypassed for Tesseract on complex layouts; prefer vision for tables and code blocks.
