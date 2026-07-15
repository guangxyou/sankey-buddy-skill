# SankeyBuddy 中文用法

## 功能

上传一份公司财报，由 SankeyBuddy 服务完成财务数据提取、资金守恒校验、
图表质量检查和渲染，最终输出 SVG 与 PNG。

支持 PDF、HTML、Excel、CSV、Word、TXT 和 Markdown，单文件不超过 20 MB。

## 基本用法

```bash
python3 scripts/sankey_buddy.py 财报.pdf --out-dir output
```

指定语言和单位：

```bash
python3 scripts/sankey_buddy.py 财报.pdf \
  --out-dir output \
  --language zh \
  --unit 亿
```

需要 Python 3.9 或更高版本。可依次尝试 `python3`、`python` 或 Windows 的
`py -3`；Skill 仅使用 Python 标准库。

## 运行提示

正常运行会依次提示：上传财报、提取并校验财务数据、SVG 已生成、本地生成
PNG 或切换服务端兜底，以及 SVG/PNG 全部完成。发生错误时会同时输出中文、
英文错误信息和机器可读错误代码。

## 常见问题

- `INVALID_SANKEY_GRAPH`：财报无法构建守恒资金流，优先换完整年度/季度报告。
- `FILE_TOO_LARGE`：文件超过 20 MB。
- 本地没有 Chrome/Chromium：客户端会自动改用服务端生成 PNG。
- 本地 PNG 生成失败：客户端会提示正在切换服务端兜底。

## 示例

### Apple

![Apple 财务桑基图](https://xslaoxu.cn/sankey/examples/apple-q2-2026.png)

### Tencent

![Tencent 财务桑基图](https://xslaoxu.cn/sankey/examples/tencent-q1-2026.png)

### 贵州茅台

![贵州茅台财务桑基图](https://xslaoxu.cn/sankey/examples/maotai-2026-q1.png)
