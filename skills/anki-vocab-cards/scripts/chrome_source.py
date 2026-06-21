#!/usr/bin/env python3
"""Return the active Chrome tab as cleaned source metadata.

Default mode reads Google Chrome with AppleScript. For tests or manual cleanup,
pass --title and --url to skip AppleScript.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from urllib.parse import urlparse


NOISE_SUFFIXES = (
    " - YouTube",
    " | YouTube",
    " - Google Chrome",
    " | Google Chrome",
    " - BBC Learning English",
    " | BBC Learning English",
    " - Wikipedia",
    " | Wikipedia",
    " - Anthropic",
    " | Anthropic",
)


def clean_title(title: str, url: str = "") -> str:
    title = re.sub(r"\s+", " ", title or "").strip()

    for suffix in NOISE_SUFFIXES:
        if title.endswith(suffix):
            title = title[: -len(suffix)].strip()

    parsed = urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.")
    if host:
        host_labels = [host]
        if "." in host:
            host_labels.append(host.split(".")[0])
        for label in host_labels:
            for sep in (" - ", " | ", " :: "):
                suffix = sep + label
                if title.lower().endswith(suffix.lower()):
                    title = title[: -len(suffix)].strip()

    title = re.sub(r"\s*[-|]\s*$", "", title).strip()
    return title or (host or url or "source")


def markdown_link(title: str, url: str) -> str:
    safe_title = title.replace("[", r"\[").replace("]", r"\]")
    safe_url = url.strip()
    return f"[{safe_title}]({safe_url})" if safe_url else safe_title


def current_chrome_tab() -> tuple[str, str]:
    script = (
        'tell application "Google Chrome" to tell active tab of front window '
        'to get title & "\\n" & URL'
    )
    proc = subprocess.run(
        ["osascript", "-e", script],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "osascript failed")

    parts = proc.stdout.rstrip("\n").split("\n", 1)
    if len(parts) != 2:
        raise RuntimeError("unexpected AppleScript output")
    return parts[0].strip(), parts[1].strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", help="Title to clean instead of reading Chrome")
    parser.add_argument("--url", help="URL to use instead of reading Chrome")
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format",
    )
    args = parser.parse_args()

    if args.title is not None or args.url is not None:
        title = args.title or ""
        url = args.url or ""
    else:
        try:
            title, url = current_chrome_tab()
        except Exception as exc:
            print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
            return 1

    cleaned = clean_title(title, url)
    markdown = markdown_link(cleaned, url)
    if args.format == "markdown":
        print(markdown)
    else:
        print(
            json.dumps(
                {
                    "title": title,
                    "url": url,
                    "clean_title": cleaned,
                    "markdown": markdown,
                },
                ensure_ascii=False,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
