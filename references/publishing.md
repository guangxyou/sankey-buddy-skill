# Publishing notes

Checked on 2026-07-14.

## Portable base package

Use the open Agent Skills layout: one directory whose required entry point is
`SKILL.md`, with optional `scripts/`, `references/`, and `assets/`. Keep the directory
and frontmatter name as `sankey-buddy-skill`; use `SankeyBuddy` only as the display name.

- Agent Skills specification: https://agentskills.io/specification
- Reference implementation: https://github.com/agentskills/agentskills

## WorkBuddy

WorkBuddy exposes community and official Skills, shows version and author, supports
updates, and performs a security scan before installation. Marketplace builds should
therefore use channel `workbuddy`, update policy `notify`, no embedded secrets, and a
minimal standard-library client.

- Marketplace: https://www.workbuddy.ai/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market
- Custom Skills: https://www.workbuddy.ai/docs/workbuddy/From-Beginner-to-Expert-Guide/Practice-Cases/Create-Skills

The current WorkBuddy custom-Skill page describes a product-specific `skill.yml`, while
its wider ecosystem also consumes Agent Skills-style packages. Keep the portable
`SKILL.md` package as the source of truth and generate a product adapter only when the
actual publisher form requires it.

## SkillHub

SkillHub accepts creator uploads and applies quality and security checks. Publish the
channel-specific ZIP with channel `skillhub`, complete bilingual usage, deterministic
outputs, and no credentials. Use semantic versions and keep old releases available for
rollback.

- Platform overview: https://skillhub.cn/about
- Publishing/community entry: https://skillhub.cn/tutorials

## Xiaohongshu

No official general-purpose `SKILL.md` runtime or Skill marketplace specification was
found. Treat Xiaohongshu as the content, demand-testing, and transaction channel rather
than a separate runtime format. Use a channel-specific direct ZIP marked
`xiaohongshu`; demonstrate real before/after charts, disclose that uploaded reports are
processed by a hosted service, and keep transactions inside the compliant shop flow
when selling later.

- Merchant onboarding: https://zhaoshang.xiaohongshu.com/
- Ecommerce: https://ec.xiaohongshu.com/ecommerce/home

## International distribution

Use the same Agent Skills package for GitHub, Claude-compatible clients, Codex,
Microsoft Agent Framework, and other compatible agents. ClawHub or marketplace-managed
packages should use notification-only updates; GitHub/direct packages can stage a
verified archive for the next run.

Do not claim universal automatic installation: the Agent Skills standard defines the
skill contents, not a single cross-platform distribution or update mechanism.
