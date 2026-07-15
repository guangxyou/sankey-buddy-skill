---
name: sankey-buddy-skill
description: Upload financial reports to SankeyBuddy, extract and validate reported financial flows, and return finished SVG and PNG Sankey charts. Use when the user asks to turn a PDF, HTML, Excel, CSV, Word, text, or Markdown financial report into a financial Sankey, income-statement flow chart, 财务桑基图, 利润表资金流向图, or revenue-to-profit visualization. Supports Chinese and English output.
metadata:
  version: 0.1.0
---

# SankeyBuddy

Use the hosted SankeyBuddy pipeline. Do not reconstruct its financial extraction,
validation, or rendering logic locally.

## Run

1. Confirm that the user supplied one supported report file. Do not upload unrelated
   documents or files containing secrets.
2. Choose the output language only when the user specifies it; otherwise use `auto`.
3. Use Python 3.9 or newer. Prefer `python3`; if unavailable, try `python` or
   `py -3`. If no compatible interpreter exists, report the prerequisite instead of
   installing system software without permission.
4. Run the bundled client:

```bash
SKILL_DIR="/absolute/path/to/sankey-buddy-skill"
python3 "$SKILL_DIR/scripts/sankey_buddy.py" \
  /absolute/path/to/report.pdf \
  --out-dir /absolute/path/to/output \
  --language auto \
  --unit auto
```

Resolve `SKILL_DIR` as the directory containing this `SKILL.md`; installation paths
vary by agent platform. Do not copy the script elsewhere.

5. Relay meaningful progress messages emitted by the client: upload, extraction and
   validation, SVG save, PNG generation, fallback when needed, and completion.
6. Treat the final JSON printed to stdout as authoritative. A run succeeds only when
   both reported `outputs.svg` and `outputs.png` exist and are non-empty.
7. Return clickable links to the SVG and PNG. Briefly mention warnings, source-report
   limitations, or simplified fallback extraction when present.

## Failure rules

- On `422`, explain that the report could not produce a conserved financial graph;
  suggest a full statutory report or a clearer income statement. Do not invent data.
- On unsupported type or size errors, report the exact limit from the client.
- If local PNG rendering is unavailable or fails, allow the client to use the hosted
  PNG fallback. Preserve the SVG if both PNG paths fail.

Read [references/usage.zh-CN.md](references/usage.zh-CN.md) for Chinese usage,
[references/usage.en.md](references/usage.en.md) for English usage, and
[references/output-examples.md](references/output-examples.md) when showing examples.
