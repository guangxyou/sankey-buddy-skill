# SankeyBuddy usage

## What it does

Upload one company financial report. The hosted SankeyBuddy service extracts the
reported financial data, validates flow conservation and chart quality, and renders
the result. The client saves both SVG and PNG.

Supported inputs are PDF, HTML, Excel, CSV, Word, TXT, and Markdown up to 20 MB.

## Commands

```bash
python3 scripts/sankey_buddy.py report.pdf --out-dir output
```

Choose output language and unit:

```bash
python3 scripts/sankey_buddy.py report.pdf \
  --out-dir output \
  --language en \
  --unit B
```

Python 3.9 or newer is required. Try `python3`, `python`, or `py -3` on Windows.
The client uses only the Python standard library.

## Progress messages

A normal run reports report upload, financial extraction and validation, SVG creation,
local PNG generation or hosted fallback, and final SVG/PNG completion. Errors include
Chinese and English messages plus a machine-readable error code.

## Troubleshooting

- `INVALID_SANKEY_GRAPH`: use a fuller statutory filing or clearer income statement.
- `FILE_TOO_LARGE`: the file exceeds 20 MB.
- No local Chrome/Chromium: the client automatically uses hosted PNG generation.
- Local PNG generation failed: the client reports that it is switching to the hosted
  fallback.

## Examples

### Apple

![Apple financial Sankey](../assets/apple-q2-2026.png)

### Tencent

![Tencent financial Sankey](../assets/tencent-q1-2026.png)

### Kweichow Moutai

![Kweichow Moutai financial Sankey](../assets/maotai-2026-q1.png)
