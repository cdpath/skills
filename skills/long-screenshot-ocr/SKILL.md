---
name: long-screenshot-ocr
description: |
  Use when the user uploads or references a long screenshot of a Feishu/Lark/web wiki page and asks to extract text, OCR, split and stitch, remove watermarks, or output Markdown. Trigger on phrases like "OCR this long screenshot", "split screenshot and OCR", "extract markdown from screenshot", "convert screenshot to markdown", or explicit mentions of overlap/deduplicate. Do not use for single short screenshots that fit in one vision call.
---

# Long-screenshot OCR

Extract a tall web/wiki screenshot into clean Markdown by splitting it into overlapping **chunks**, reading each chunk, **stitching** the text, and stripping UI **noise**.

## Hard Rules

- Do not run Tesseract, EasyOCR, PaddleOCR, OCRmyPDF, or any other local OCR engine unless the user explicitly asks for local/no-vision OCR.
- Do not check whether Tesseract or OCR language packs are installed in the normal path.
- If image reading is not available to the current model/session after chunks are read, stop and tell the user to rerun with a vision-capable model/session. Do not compensate with local OCR.

## Steps

1. **Resolve paths.**
   - Set `skill_dir` to the "Base directory for this skill" path shown when the skill loads.
   - Resolve the input screenshot path from the user's argument.
   - Set the final Markdown path by replacing the input screenshot extension with `.md`, unless the user gave an explicit output path.
   - Completion criterion: you know `skill_dir`, `input_image`, and `output_md`.

2. **Inspect and split with the bundled script.**
   - Run the bundled splitter first:
     `python3 "$skill_dir/scripts/split_long_screenshot.py" "$input_image"`.
   - Do not write ad hoc Python, heredocs, or shell loops for dimensions or slicing. The bundled script already inspects the image, chooses importable Pillow or existing `ffmpeg`/`ffprobe`, creates the temp directory, and saves chunk files.
   - If the script reports that neither Pillow nor ffmpeg is available, run the same script once through:
     `uvx --with pillow python "$skill_dir/scripts/split_long_screenshot.py" "$input_image"`.
   - Do not run `pip install`, create a venv, or install persistent dependencies.
   - Completion criterion: the script output records width, height, format, `out_dir`, and chunk count; the last chunk ends exactly at the image height and adjacent chunks share 500 px overlap.

3. **Read every chunk.**
   - Use the current model's vision capability to transcribe each chunk, preserving headings, tables, lists, and fenced code blocks.
   - Do not install, check, or run third-party OCR tools in the normal path. Reading the chunk images is the OCR step.
   - If you cannot actually inspect the chunk images, stop with a short explanation instead of trying local OCR.
   - Completion criterion: every chunk has a corresponding raw text excerpt.

4. **Stitch and deduplicate.**
   - Align adjacent chunks using their 500 px overlap.
   - Keep one copy of each duplicated paragraph; drop broken fragments that span the boundary.
   - Completion criterion: reading the stitched text from top to bottom flows naturally with no repeated adjacent paragraphs.

5. **Strip noise.**
   - Remove: page header, company/confidentiality banners, left sidebar, right-side AI/action buttons, bottom "你可能还想问" widget, "真诚点赞，手留余香" footer, and page-number watermarks.
   - Completion criterion: only the main document content remains.

6. **Format and save.**
   - Convert into Markdown with `#`/`##` headings, `|` tables, ` ``` ` code blocks, and `-`/`1.` lists.
   - Save the final Markdown at `output_md`, next to the input image with the extension replaced by `.md`.
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
| OCR fallback | None by default | Stop if vision is unavailable unless the user explicitly asks for local OCR. |

### Tools

- [`scripts/split_long_screenshot.py`](scripts/split_long_screenshot.py) for image inspection and slicing.
- `uvx --with pillow` for one-shot slicing only when no local image tool is available.
- Vision capability for the primary transcription path.

### Failure modes

- **Repeated paragraphs** — overlap was not used or deduplication was skipped; fix by re-checking the 500 px overlap.
- **Missing boundary text** — chunk height too large or overlap too small; verify chunks cover the full height and share overlap.
- **UI noise in output** — the strip-noise step was skipped; re-run step 6 against the full stitched text.
- **Garbled tables/code** — local OCR was used on complex layouts; stop and rerun with vision unless the user explicitly requested local OCR.
- **Ad hoc image scripts** — the bundled script was ignored; rerun `scripts/split_long_screenshot.py` instead of writing new Python or shell crop code.
- **Slow dependency setup** — local tools were not checked through the bundled script first; use the bundled script and only then a one-shot `uvx --with pillow` command.
- **Wrong output filename** — the document title was used; rename final output from the input screenshot basename with `.md`.
