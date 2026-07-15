# Privacy summary / 隐私摘要

## 中文

SankeyBuddy 必须把用户选择的财报上传到托管服务，才能进行文本解析、AI 财务数据
提取、守恒校验和 SVG 渲染。客户端只应上传用户明确指定的单个文件。

Beta 客户端还会发送 Skill 版本、分发渠道、协议版本和随机匿名安装 ID。服务端记录
匿名安装 ID 的短哈希，不记录本地用户名、设备名或文件所在目录。这些元数据用于统计
渠道需求、成功率和版本分布，并为未来按成功生成次数计费预留接口。

当前代码使用内存上传；在没有单独公布并部署正式隐私政策和留存机制前，不应宣称
“永不留存”或“符合某项认证”。公开发布前应在产品域名提供正式隐私政策、服务条款、
删除请求入口和联系方式。

## English

SankeyBuddy uploads the one report explicitly selected by the user to its hosted
service for text parsing, AI extraction, conservation validation, and SVG rendering.

The beta client also sends its skill version, distribution channel, protocol version,
and a random anonymous install ID. The server logs a short hash of that ID, not the
local username, device name, or source directory. These metadata measure channel
demand, success rates, and version adoption and reserve a future per-success billing
hook.

The current code uses in-memory upload handling. Do not claim permanent non-retention
or regulatory certification until a production privacy policy and retention process
are published and deployed. Before public release, provide a privacy-policy URL,
terms, a deletion-request route, and support contact details on the product domain.
