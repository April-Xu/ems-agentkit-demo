# 部署指南：EMS AgentKit Demo

这份指南将合成 EMS 演示部署到你自己的火山引擎账号。默认只读取仓库里的飞书多维表格快照，SimplyBook 为 mock，执行结果也为 mock；不会写入 SimplyBook 或同步 Impact Key。

## 部署拓扑与边界

| 组件 | 部署位置 | 演示边界 |
|---|---|---|
| EMS MCP + 治理后端 | AgentKit MCP Gateway，自定义镜像 | 读取合成快照；含只读 SimplyBook 适配器、临时 Grant、Change Set 准备/冻结/审批提交工具 |
| 排期检查 Agent | AgentKit Runtime | 独立只读 A2A Agent，检查重复、排期冲突、容量和数据问题 |
| EMS 编排 Agent | AgentKit Runtime | 连接 MCP 与排期检查 Agent；不暴露业务写工具 |
| Reviewer / Worker 路由 | 本地 MCP 后端 | 仅用于本机隔离审批与模拟执行；AgentKit Gateway 只发布 `/mcp`，不会把 Reviewer 或 Worker HTTP 路由暴露到公网 |

这里的 `demo.operator` 是服务端配置的合成主体，不代表员工 SSO。演示审批不是飞书审批。生产身份、飞书审批回调、SimplyBook 写入、Impact Key 同步、邮件发送、数据库审计留存和定时巡检都没有接入。云端 MCP 运行状态使用容器内临时 SQLite；本地 Reviewer/Worker 使用本机独立 SQLite，两边状态不共享，云端重启后状态也不会持久保留。

## 前置条件

1. 已开通 AgentKit 的火山引擎账号，并有 `default` 项目下的 Runtime、MCP Gateway、TOS、镜像仓库和持续交付权限；同时已开通方舟模型服务，并能调用 `.env` 中配置的模型。
2. AgentKit CLI、Python 3.12、`uv`；云端构建使用 AgentKit Build，不要求本机安装 Docker。
3. macOS/Linux shell。`.env` 保存部署参数和密钥，已被 Git 忽略。

AgentKit CLI 安装与 Runtime 部署见[官方 CLI 部署文档](https://docs.volcengine.com/docs/AgentKit/Creating_runtime_via_CLI_tool?lang=en)，MCP 接入方式见[官方 MCP 接入文档](https://docs.volcengine.com/docs/agentkit/Integrating_MCP_service_in_agent?lang=zh)。仓库示例按 AgentKit CLI 0.54.x 编写；CLI 参数若有变化，以本机 `agentkit --help` 为准。

Runtime 显式设置 `MODEL_AGENT_NAME` 和 `MODEL_ENDPOINT`。默认模型为 `doubao-seed-2-1-pro-260628`；若当前账号未开通该模型，请在 `.env` 中改为账号可调用的模型名称。方舟模型服务和模型调用权限是 Agent 在线回复的前置条件。

VeADK 与编排 Agent 当前使用 Google ADK 1.x；requirements 将版本限制在 `>=1.34,<2.0`，避免 2.x 的不兼容 API 变化。VeADK 的[官方依赖变更](https://github.com/volcengine/veadk-python/commit/c2ed301)设定了 1.34 的下限；AgentKit SDK 用到的 A2A executor 配置模块可在[Google ADK 1.39.1 源码](https://github.com/google/adk-python/blob/v1.39.1/src/google/adk/a2a/executor/config.py)中核对。

## 1. 获取仓库并准备本地配置

```bash
git clone https://github.com/April-Xu/ems-agentkit-demo.git
cd ems-agentkit-demo
cp .env.example .env
chmod 600 .env
```

在 `.env` 中为以下 3 个变量各生成一个互不相同的随机值：

- `EMS_DEMO_GRANT_REVIEWER_KEY`
- `EMS_DEMO_CHANGESET_REVIEWER_KEY`
- `EMS_DEMO_WORKER_KEY`

可以用 `openssl rand -hex 32` 生成。它们仅用于演示容器中的模拟 Reviewer 和 Worker，不要复用 MCP/API Key。按顺序登录并检查 CLI：

```bash
export PATH="$HOME/.local/bin:$PATH"
agentkit --version
agentkit login --console --provider volcengine
agentkit whoami
```

## 2. 通过 AgentKit 云构建发布 MCP 镜像

```bash
scripts/build-mcp-image-agentkit.sh
```

脚本把 MCP 服务和合成表格快照复制到被 Git 忽略的 `.deploy/mcp-image/`，调用 AgentKit Build 在云端构建并推送到当前账号的 Container Registry，并将生成的镜像地址写入本地 `.env` 的 `EMS_MCP_IMAGE`。构建过程及所需云资源配置见 `services/ems-governance/agentkit-build.yaml`。该流程不读取客户数据或 `.env` 密钥。

若你已有 Docker Buildx 和镜像仓库，也可以用 `scripts/build-push-mcp.sh` 自行构建并推送。

## 3. 创建 MCP Gateway 服务

执行前先载入本地配置：

```bash
set -a
source .env
set +a
```

然后创建服务。API Key 由 Gateway 管理；Reviewer/Worker Key 仅注入后端，不提供给 Agent：

```bash
agentkit mcp service create \
  --name ems-impact-week-demo \
  --description "Synthetic EMS MCP and governance demo" \
  --project default \
  --region cn-beijing \
  --backend-type custom-private \
  --image-url "$EMS_MCP_IMAGE" \
  --command "python /app/server.py" \
  --path /mcp \
  --protocol mcp \
  --gateway-mode Shared \
  --inbound-auth api-key \
  --inbound-api-key-name ems-agent \
  --env "EMS_DEMO_GRANT_REVIEWER_KEY=$EMS_DEMO_GRANT_REVIEWER_KEY" \
  --env "EMS_DEMO_CHANGESET_REVIEWER_KEY=$EMS_DEMO_CHANGESET_REVIEWER_KEY" \
  --env "EMS_DEMO_WORKER_KEY=$EMS_DEMO_WORKER_KEY"
```

到 AgentKit 控制台打开 `ems-impact-week-demo` 的详情页，记录“访问域名”以及调用示例里的完整 MCP Endpoint 和 API Key。Endpoint 通常形如 `https://<gateway-host>/mcp`。把 Endpoint 和 API Key 分别写入本地 `.env` 的 `EMS_DEMO_MCP_URL`、`EMS_DEMO_MCP_AUTH_KEY`；不要提交这两个值到 GitHub。

### 配置 MCP SDK 的公网 Host allowlist

MCP SDK 的 DNS rebinding 防护默认只接受本机 Host。Gateway 首次创建后会分配公网域名，所以还要把**这个服务实际的域名**加入后端 allowlist：

1. 在服务详情的“基本信息”页点击“后端服务 > 编辑”。
2. 在环境变量中添加 `EMS_MCP_ALLOWED_HOSTS`，值填写“访问域名”里的主机名，例如 `abc.apigateway-cn-beijing.volceapi.com`；只填主机名，不带 `https://`、路径或通配符。
3. 若控制台的 MCP 工具页会从浏览器直连，可将 `EMS_MCP_ALLOWED_ORIGINS` 设为 `https://console.volcengine.com`。命令行客户端一般不发送 Origin，可保持为空。
4. 保存后等待滚动重启完成。不要关闭 DNS rebinding protection，也不要使用全域名通配符。

这个域名必须精确匹配当前 MCP Gateway。更换 Gateway 域名后，需同步更新环境变量并重启后端。

## 4. 验证 MCP 工具发现

`.env` 已载入后运行：

```bash
scripts/check-mcp-tools.sh
```

成功时会打印 MCP 工具名。至少应包含 `list_events`、`simplybook_list_calendars`、`request_temporary_grant`、`prepare_change_set`、`freeze_change_set` 和 `submit_change_set_approval`；不应出现报名写入、取消、邮件发送或 Impact Key 写入工具。若返回 `421 Invalid Host header`，请检查 `EMS_MCP_ALLOWED_HOSTS` 是否仅填了域名、是否与 Gateway 的访问域名一致，以及服务滚动重启是否完成。

## 5. 部署排期检查 Agent 和编排 Agent

先部署只读 A2A 排期检查 Agent：

```bash
scripts/deploy-agent.sh schedule-checker
```

在 AgentKit 控制台的 Runtime 详情中，将 Agent Card URL、Runtime API Key 和公网入口 URL 分别填入 `.env` 的：

- `EMS_SCHEDULE_CHECKER_AGENT_CARD_URL`
- `EMS_SCHEDULE_CHECKER_A2A_AUTH_KEY`
- `EMS_SCHEDULE_CHECKER_PUBLIC_URL`

然后再次运行脚本，使 Agent Card 使用真实公网入口：

```bash
scripts/deploy-agent.sh schedule-checker
```

如需使用其它模型，在 `.env` 中设置 `MODEL_AGENT_NAME` 与 `MODEL_ENDPOINT`，重新运行对应部署脚本。默认模型需已在当前账号开通；模型不可用时，Runtime 可能显示 `Ready`，但在线调用会失败。

确认 Runtime Ready 后，部署编排 Agent：

```bash
scripts/deploy-agent.sh orchestrator
```

然后在 Runtime 副本目录调用一次只读演示任务：

```bash
cd .deploy/orchestrator
agentkit status --config-file agentkit.yaml --verbose
agentkit invoke run --config-file agentkit.yaml \
  "只为 DEMO-IW-2026-001 / BATCH-DEMO-001 申请临时 Grant。返回授权状态后停止；如果状态不是 Active，不要读取数据、准备变更或执行写入。"
agentkit runtime logs ems-iw-demo-orchestrator --limit 100
```

云端编排 Agent 请求临时 Grant 后，预期停在 `PENDING_APPROVAL`。这是当前公开 MCP Gateway 的安全边界：Gateway 只路由 `/mcp`，没有公网 Reviewer API 或飞书审批回调，因此不能在云端批准该 Grant，也不能继续为这份云端 Grant 生成 Change Set。不要用本机 Reviewer 去审批云端的 ID。

部署脚本会将 Agent 项目复制到被忽略的 `.deploy/` 目录。AgentKit 会在配置副本里写入 Runtime ID、Endpoint 等部署状态；不要将 `.deploy/` 加入 Git。

## 6. 本地演示 Reviewer 与 Worker 流程

Reviewer 和 Worker HTTP 路由仅供本地演示，不会经由 AgentKit Gateway 对外发布。Reviewer/Worker Key 不放入 Agent Runtime。可在本地启动 MCP 服务并演示隔离审批：

```bash
scripts/run-local-mcp.sh
```

本地实例会使用独立的 `/tmp/ems-agentkit-demo.sqlite3`。它只能处理本地 MCP 创建的 Grant 和 Change Set，与上一步云端服务的临时数据库完全分开。此流程只用于演示审批闸门和 mock Worker，不代表云端或飞书审批已经连通。

新终端载入 `.env` 后，使用以下路由查询待审项、批准 Grant、批准冻结的 Change Set，再调用模拟 Worker。审批人分两把 Reviewer Key；Worker 还需要自己的 Key。执行结果固定为 `SIMULATED`，SimplyBook 与 Impact Key 字段均标记未发送/未同步。

```bash
curl http://127.0.0.1:8000/demo/reviewer/queue \
  -H "Authorization: Bearer $EMS_DEMO_GRANT_REVIEWER_KEY"

curl -X POST http://127.0.0.1:8000/demo/reviewer/grants/<GRANT_ID>/approve \
  -H "Authorization: Bearer $EMS_DEMO_GRANT_REVIEWER_KEY"

curl -X POST http://127.0.0.1:8000/demo/reviewer/change-sets/<CHANGE_SET_ID>/approve \
  -H "Authorization: Bearer $EMS_DEMO_CHANGESET_REVIEWER_KEY"

curl -X POST http://127.0.0.1:8000/internal/change-sets/<CHANGE_SET_ID>/execute \
  -H "Authorization: Bearer $EMS_DEMO_WORKER_KEY" \
  -H "Idempotency-Key: demo-run-20260928-000001" \
  -H "Content-Type: application/json" \
  --data '{"expectedVersion":1,"expectedHash":"<FROZEN_HASH>"}'
```

## 回滚演示资源

只删除本 POC 创建的对应资源；删除前在控制台核对资源名称。

```bash
agentkit runtime delete ems-iw-demo-orchestrator --yes --region cn-beijing
agentkit runtime delete ems-iw-demo-schedule-checker --yes --region cn-beijing
agentkit mcp service delete ems-impact-week-demo --yes --project default --region cn-beijing
```

另外在 Container Registry 删除这次 POC 的镜像版本和专用仓库资源。

## 后续对接需客户确认

- Feishu Base 的正式读取身份与 API 权限；当前镜像加载仓库内快照，表格变更不会自动同步。
- 员工登录身份如何可信传递到 EMS 治理服务，以及 Grant 策略。
- Feishu Grant/Change Set 审批定义、审批人、回调验签；如需云端完整审批，还需部署具备共享持久化状态的 Reviewer 服务或实现 Feishu 审批回调。
- SimplyBook 非生产环境、API 凭据及按人报名/取消/改期接口；现有批量接口按数量操作，无法确认报名人与 booking 的绑定，所有写操作仍为 mock。
- Impact Key 同步接口与幂等/回查方式；当前仅返回 mock projection 状态。
- 云端私有 Worker、持久数据库、审计留存、任务重试/告警，及邮件发送接口和发送审批策略。
