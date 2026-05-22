#!/usr/bin/env python3
"""Normalize visible English straight quotes to Chinese quote marks.

Defaults are conservative for Markdown: skip frontmatter, fenced code blocks,
inline code spans, and HTML/XML tags.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from typing import Iterable


TEXT_EXTENSIONS = {".md", ".markdown", ".mdx", ".txt"}


def is_probable_tag_start(text: str, index: int) -> bool:
    if text[index] != "<" or index + 1 >= len(text):
        return False
    nxt = text[index + 1]
    return nxt.isalpha() or nxt in {"/", "!", "?"}


def consume_tag(text: str, index: int) -> int:
    quote = None
    i = index + 1
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == quote:
                quote = None
        elif ch in {"'", '"'}:
            quote = ch
        elif ch == ">":
            return i + 1
        i += 1
    return index + 1


def consume_backticks(text: str, index: int) -> int:
    tick_count = 0
    while index + tick_count < len(text) and text[index + tick_count] == "`":
        tick_count += 1
    marker = "`" * tick_count
    close = text.find(marker, index + tick_count)
    if close == -1:
        return index + tick_count
    return close + tick_count


def convert_segment(segment: str, state: dict[str, bool], include_single: bool) -> str:
    out: list[str] = []
    i = 0
    while i < len(segment):
        ch = segment[i]

        if ch == "\\" and i + 1 < len(segment) and segment[i + 1] == '"':
            out.append("“" if not state["double_open"] else "”")
            state["double_open"] = not state["double_open"]
            i += 2
            continue

        if ch == '"':
            out.append("“" if not state["double_open"] else "”")
            state["double_open"] = not state["double_open"]
            i += 1
            continue

        if include_single and ch == "'":
            prev_ch = segment[i - 1] if i > 0 else ""
            next_ch = segment[i + 1] if i + 1 < len(segment) else ""
            if prev_ch.isalnum() and next_ch.isalnum():
                out.append(ch)
            else:
                out.append("‘" if not state["single_open"] else "’")
                state["single_open"] = not state["single_open"]
            i += 1
            continue

        out.append(ch)
        i += 1

    return "".join(out)


def convert_line(line: str, state: dict[str, bool], include_single: bool) -> str:
    out: list[str] = []
    i = 0
    text_start = 0

    def flush(until: int) -> None:
        nonlocal text_start
        if until > text_start:
            out.append(convert_segment(line[text_start:until], state, include_single))
        text_start = until

    while i < len(line):
        if line[i] == "`":
            flush(i)
            end = consume_backticks(line, i)
            out.append(line[i:end])
            i = end
            text_start = i
            continue

        if is_probable_tag_start(line, i):
            flush(i)
            end = consume_tag(line, i)
            out.append(line[i:end])
            i = end
            text_start = i
            continue

        i += 1

    flush(len(line))
    return "".join(out)


def fence_marker(line: str) -> tuple[str, int] | None:
    stripped = line.lstrip(" ")
    if len(line) - len(stripped) > 3:
        return None
    if stripped.startswith("```"):
        return ("`", len(stripped) - len(stripped.lstrip("`")))
    if stripped.startswith("~~~"):
        return ("~", len(stripped) - len(stripped.lstrip("~")))
    return None


def normalize_text(text: str, include_single: bool = False) -> tuple[str, dict[str, bool]]:
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    state = {"double_open": False, "single_open": False}
    in_fence = False
    fence_char = ""
    fence_len = 0
    in_frontmatter = False

    if lines and lines[0].strip() == "---":
        in_frontmatter = True

    for line_number, line in enumerate(lines):
        if in_frontmatter:
            out.append(line)
            if line_number > 0 and line.strip() in {"---", "..."}:
                in_frontmatter = False
            continue

        marker = fence_marker(line)
        if marker:
            char, length = marker
            if in_fence and char == fence_char and length >= fence_len:
                in_fence = False
                fence_char = ""
                fence_len = 0
            elif not in_fence:
                in_fence = True
                fence_char = char
                fence_len = length
            out.append(line)
            continue

        if in_fence:
            out.append(line)
            continue

        out.append(convert_line(line, state, include_single))

    return "".join(out), state


def iter_targets(paths: Iterable[str]) -> list[Path]:
    files: list[Path] = []
    for raw_path in paths:
        path = Path(raw_path).expanduser()
        if path.is_dir():
            for root, dirnames, filenames in os.walk(path):
                dirnames[:] = [d for d in dirnames if d not in {".git", "node_modules", ".venv", "venv"}]
                for filename in filenames:
                    candidate = Path(root) / filename
                    if candidate.suffix.lower() in TEXT_EXTENSIONS:
                        files.append(candidate)
        else:
            files.append(path)
    return sorted(dict.fromkeys(files))


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert visible straight quotes to Chinese quote marks.")
    parser.add_argument("paths", nargs="+", help="Files or directories to process")
    parser.add_argument("--write", action="store_true", help="Write changes to files")
    parser.add_argument("--check", action="store_true", help="Exit 1 if any file would change")
    parser.add_argument("--single", action="store_true", help="Also convert likely paired straight single quotes")
    args = parser.parse_args()

    changed = []
    warnings = []

    for path in iter_targets(args.paths):
        if not path.exists():
            warnings.append(f"missing: {path}")
            continue
        if not path.is_file():
            warnings.append(f"not a file: {path}")
            continue

        try:
            original = read_text_file(path)
        except UnicodeDecodeError:
            warnings.append(f"skip non-UTF-8 file: {path}")
            continue

        normalized, state = normalize_text(original, include_single=args.single)
        if normalized != original:
            changed.append(path)
            if args.write:
                path.write_text(normalized, encoding="utf-8")
        if state["double_open"]:
            warnings.append(f"unmatched double quote after processing: {path}")
        if args.single and state["single_open"]:
            warnings.append(f"unmatched single quote after processing: {path}")

    for path in changed:
        print(f"{'updated' if args.write else 'would update'}: {path}")
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)

    if args.check and changed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
