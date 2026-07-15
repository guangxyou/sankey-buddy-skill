# SankeyBuddy 中文用法

## 功能

上传一份公司财报，由 SankeyBuddy 服务完成财务数据提取、资金守恒校验、
图表质量检查和渲染，最终输出 SVG 与 1920×1200 PNG。

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

仅检查版本：

```bash
python3 scripts/sankey_buddy.py --check-version
```

直接安装包默认采用“下次生效”升级策略。若希望当前任务开始前自动升级：

```bash
python3 scripts/sankey_buddy.py 财报.pdf --out-dir output --update-policy auto
```

## 隐私与计费

- 财报会上传到 SankeyBuddy 服务处理；服务当前按现有产品策略在内存中处理文件。
- 客户端会发送 Skill 版本、分发渠道和随机匿名安装 ID，用于判断需求来源和版本分布。
- 不发送用户名、设备名或本地目录。服务端只保存匿名安装 ID 的哈希摘要。
- 当前 Beta 免费，不扣次数。接口已预留“成功生成一张图”为未来计费单位。
- SankeyBuddy 生成结果用于数据可视化，不构成投资、审计或会计意见；重要数字应回查原始财报。

## 常见问题

- `INVALID_SANKEY_GRAPH`：财报无法构建守恒资金流，优先换完整年度/季度报告。
- `FILE_TOO_LARGE`：文件超过 20 MB。
- `PNG_RENDERER_NOT_FOUND`：安装 Chrome/Chromium，或通过 `--chrome` 指定路径。
- 只有 SVG 没有 PNG：SVG 可以保留使用，但任务尚未满足完整交付要求。
