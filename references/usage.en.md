# SankeyBuddy usage

## What it does

Upload one company financial report. The hosted SankeyBuddy service extracts the
reported financial data, validates flow conservation and chart quality, and renders
the result. The client saves both SVG and a 1920×1200 PNG.

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

Check the installed version without uploading a report:

```bash
python3 scripts/sankey_buddy.py --check-version
```

Direct packages stage verified updates for the next invocation by default. Use
`--update-policy auto` to apply an available update before the current report is sent.

## Privacy and billing

- The report is uploaded to the SankeyBuddy service for processing.
- The client sends its version, distribution channel, and a random anonymous install
  ID so the beta can measure channel demand and version adoption.
- It does not send the local username, device name, or source directory. The server
  logs only a short hash of the anonymous install ID.
- The beta is free. The response already exposes a future billing unit of one
  successfully generated chart, but no credits are currently charged.
- SankeyBuddy is a visualization aid, not investment, audit, or accounting advice.
  Verify material figures against the source filing.

## Troubleshooting

- `INVALID_SANKEY_GRAPH`: use a fuller statutory filing or clearer income statement.
- `FILE_TOO_LARGE`: the file exceeds 20 MB.
- `PNG_RENDERER_NOT_FOUND`: install Chrome/Chromium or pass `--chrome PATH`.
- SVG exists but PNG failed: preserve the SVG, but do not report full completion.
