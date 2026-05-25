---
name: chinese-quote-normalizer
description: Convert English straight quote marks to Chinese typography in Chinese-language writing. Use when the user asks to replace English-state quotes, straight quotes, ASCII quotes, or Markdown/Feishu/Lark document quotes with Chinese quote marks; especially for .md, .markdown, .mdx, .txt files, pasted Chinese text, or Feishu/Lark docs where visible text should use “...” instead of "..." while preserving code, attributes, and document structure.
---

# Chinese Quote Normalizer

## Goal

Replace visible English straight double quotes with Chinese curved quotes:

- `"内容"` -> `“内容”`

Optionally replace straight single quotes when the user explicitly asks:

- `'内容'` -> `‘内容’`

Default to double quotes only. Preserve code syntax, Markdown structure, XML/HTML tag attributes, and Feishu/Lark document block structure.

## Local Markdown/Text Files

Use the bundled script for local files. Paths below are relative to this
skill's own directory; run them from the skill folder, or prefix with the
skill's absolute path on the current machine.

```bash
python3 scripts/normalize_quotes.py --write <file-or-directory>
```

Useful modes:

```bash
# Preview only
python3 scripts/normalize_quotes.py <file-or-directory>

# Fail if changes would be needed
python3 scripts/normalize_quotes.py --check <file-or-directory>

# Also convert likely paired single quotes
python3 scripts/normalize_quotes.py --write --single <file-or-directory>
```

The script recursively processes Markdown-like files in directories (`.md`, `.markdown`, `.mdx`, `.txt`) and skips:

- YAML frontmatter at the top of Markdown files
- fenced code blocks
- inline code spans
- HTML/XML tags and their attributes

After writing, run `--check` or re-run preview to confirm no remaining visible straight double quotes.

## Feishu/Lark Docs

Use `lark-doc` first for Feishu/Lark URLs. Do not overwrite the whole document just to replace quotes.

Workflow:

1. Fetch the document as full XML:

   ```bash
   lark-cli docs +fetch --api-version v2 --doc "<url-or-token>" --detail full --format json
   ```

2. Extract only visible text segments outside XML tags. Ignore `id="..."`, width attributes, URLs, tokens, and other tag attributes.

3. Find paired straight double quote phrases in visible text with a pattern equivalent to:

   ```regex
   "([^"]*)"
   ```

4. For each unique phrase, replace it with Chinese quotes using `str_replace`:

   ```bash
   lark-cli docs +update --api-version v2 --doc "<url-or-token>" \
     --command str_replace \
     --pattern "<regex-escaped-original-phrase>" \
     --content "“内容”"
   ```

   Regex-escape metacharacters in the original phrase, including `+`, `.`, `?`, `(`, `)`, `[`, `]`, `{`, `}`, `|`, `^`, `$`, `*`, and `\`.

5. If a full phrase fails to change because of regex or document matching behavior, replace the left and right halves in sequence, for example:

   ```bash
   lark-cli docs +update --api-version v2 --doc "<url-or-token>" \
     --command str_replace --pattern '"关键词开头' --content '“关键词开头'

   lark-cli docs +update --api-version v2 --doc "<url-or-token>" \
     --command str_replace --pattern '关键词结尾"' --content '关键词结尾”'
   ```

6. Fetch again and validate only visible text:

   - remaining visible `"` count is `0`
   - `“` count equals `”` count

## Pasted Text

For pasted Chinese prose, convert paired straight double quotes directly:

1. Scan left to right outside code blocks/spans if Markdown is present.
2. Alternate opening and closing marks: first `"` -> `“`, next `"` -> `”`.
3. Keep unmatched quotes visible in the result only if the source text has an odd quote count; mention the ambiguity.

## Safety Notes

- Do not convert quotes inside programming code, JSON, shell commands, YAML frontmatter, XML/HTML attributes, or Markdown inline code unless the user explicitly asks to normalize code too.
- Treat apostrophes in English words (`don't`, `user's`) as apostrophes, not Chinese single quotes.
- For live Feishu/Lark documents, always refetch and validate after edits.
