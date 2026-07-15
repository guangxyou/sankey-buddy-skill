---
name: sankey-buddy-skill
description: Upload financial reports to SankeyBuddy, extract and validate reported financial flows, and return finished SVG and PNG Sankey charts. Use when the user asks to turn a PDF, HTML, Excel, CSV, Word, text, or Markdown financial report into a financial Sankey, income-statement flow chart, 财务桑基图, 利润表资金流向图, or revenue-to-profit visualization. Supports Chinese and English output.
---

# SankeyBuddy

Use the hosted SankeyBuddy pipeline. Do not reconstruct its financial extraction,
validation, or rendering logic locally.

## Run

1. Confirm that the user supplied one supported report file. Do not upload unrelated
   documents or files containing secrets.
2. Choose the output language only when the user specifies it; otherwise use `auto`.
3. Run the bundled client:

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

4. Relay meaningful progress messages emitted by the client: version check, upload,
   extraction and validation, SVG save, PNG rendering, and completion.
5. Treat the final JSON printed to stdout as authoritative. A run succeeds only when
   both reported `outputs.svg` and `outputs.png` exist and are non-empty.
6. Return clickable links to the SVG and PNG. Briefly mention warnings, source-report
   limitations, or simplified fallback extraction when present.

## Version and billing behavior

- Check the service manifest before every upload. The client does this automatically.
- Respect marketplace-managed updates. WorkBuddy, SkillHub, and ClawHub builds notify
  the user and let the marketplace update the package.
- For direct or Xiaohongshu-distributed builds, use the manifest policy. `next-run`
  stages a verified update after this job and applies it on the next invocation;
  `auto` applies it before processing the report. Never install an archive without a
  matching SHA-256 digest.
- The current beta is free. Still send the anonymous install ID and distribution
  channel so demand can be measured. Never fabricate, expose, or request an API key.
- If a future response says payment is required, stop and explain the quoted price or
  required credits before asking the user to authorize a purchase.

## Failure rules

- On `422`, explain that the report could not produce a conserved financial graph;
  suggest a full statutory report or a clearer income statement. Do not invent data.
- On unsupported type or size errors, report the exact limit from the client.
- If SVG succeeds but local PNG rendering fails, preserve and return the SVG, explain
  that Chrome/Chromium is required, and do not claim complete PNG delivery.
- Never retry a billable request automatically. During the free beta, retry network
  timeouts at most once when the client explicitly reports that no result was created.

Read [references/usage.zh-CN.md](references/usage.zh-CN.md) for Chinese usage,
[references/usage.en.md](references/usage.en.md) for English usage, and
[references/output-examples.md](references/output-examples.md) when showing examples.
Read [references/privacy.md](references/privacy.md) before answering privacy or data
retention questions.
