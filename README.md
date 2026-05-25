# Chinese Quote Normalizer / 中文引号规范化

把中文写作里的**英文直引号**自动转成**中文弯引号**，让排版更地道。

```
"内容"  ->  “内容”      （双引号，默认）
'内容'  ->  ‘内容’      （单引号，需显式开启）
```

它足够「聪明」：只改可见正文里的引号，**自动跳过代码、frontmatter、HTML 标签、英文缩写撇号**等不该动的地方，避免把 `don't`、`<a href="...">`、代码字符串里的引号也误改。

---

## ✨ 特点

- **零依赖**：纯 Python 3 标准库，单文件脚本，拿来即用。
- **保守安全**：默认只转双引号；处理 Markdown 时自动跳过
  - 顶部 YAML frontmatter（`---` 之间）
  - 围栏代码块（```` ``` ```` 和 `~~~`）
  - 行内代码（`` `code` ``）
  - HTML/XML 标签及其属性（如 `id="..."`）
- **配对识别**：按出现顺序在「开引号 `“`」「闭引号 `”`」之间交替，处理完会提示是否有落单的引号。
- **英文撇号不误伤**：`don't`、`user's` 里的 `'` 当作撇号保留。
- **多种用法**：本地文件批处理、飞书/Lark 文档、直接粘贴的文本三种场景。
- **可作为 Codex / Agent 技能**调用。

---

## 📁 项目结构

```
chinese-quote-normalizer/
├── SKILL.md                      # 技能说明（供 AI Agent 阅读调用）
├── agents/
│   └── openai.yaml               # OpenAI / Codex 技能接口配置
└── scripts/
    └── normalize_quotes.py       # 核心转换脚本（零依赖）
```

---

## 🚀 用法一：命令行脚本（处理本地文件）

环境要求：Python 3.8+，无需安装任何依赖。

```bash
# 预览：只显示哪些文件会被修改，不写入
python3 scripts/normalize_quotes.py <文件或目录>

# 写入：实际修改文件
python3 scripts/normalize_quotes.py --write <文件或目录>

# 校验：若有文件需要修改则以退出码 1 结束（适合接入 CI / pre-commit）
python3 scripts/normalize_quotes.py --check <文件或目录>

# 同时转换成对的单引号
python3 scripts/normalize_quotes.py --write --single <文件或目录>
```

传入目录时会**递归**处理其中的 `.md`、`.markdown`、`.mdx`、`.txt` 文件，并自动跳过 `.git`、`node_modules`、`.venv`、`venv` 等目录。

写入后，可再跑一次 `--check` 或预览，确认正文里已没有残留的英文直引号。

---

## 🚀 用法二：作为 Codex / Agent 技能

本仓库带有 `agents/openai.yaml`，可作为技能挂载到 Agent 中，直接用自然语言调用：

```
Use $chinese-quote-normalizer to convert English straight quotes in this Markdown file to Chinese quote marks.
```

安装为 Codex 技能后，脚本通常位于：

```
~/.codex/skills/chinese-quote-normalizer/scripts/normalize_quotes.py
```

更详细的 Agent 调用规范见 [`SKILL.md`](SKILL.md)。

---

## 🚀 用法三：飞书 / Lark 文档

针对飞书/Lark 在线文档，**不要整篇覆盖**，而是定位可见文本中的成对直引号逐段替换，避免破坏文档结构。完整工作流（基于 `lark-cli`）见 [`SKILL.md`](SKILL.md) 的「Feishu/Lark Docs」一节，核心步骤：

1. 拉取文档完整 XML；
2. 只在 XML 标签外的可见文本里找成对的 `"..."`；
3. 用 `str_replace` 逐个替换为 `“...”`；
4. 重新拉取校验：残留可见 `"` 数为 0，且 `“` 与 `”` 数量相等。

---

## 🛡️ 不会动这些（安全边界）

- 编程代码、JSON、Shell 命令、YAML frontmatter、XML/HTML 属性、Markdown 行内代码中的引号——除非你明确要求一起规范化。
- 英文单词里的撇号（`don't`、`user's`）当作撇号，不会变成中文单引号。
- 飞书/Lark 在线文档每次改完都会重新拉取并校验。

---

## 📄 License

MIT
