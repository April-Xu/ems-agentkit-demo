# 部署指南：EMS AgentKit Demo

这份指南把仓库里的演示脚手架部署到自己的火山引擎账号。**它部署的是演示环境**：MCP 后端默认读仓库里的合成多维表快照，SimplyBook 默认 mock；执行端只返回模拟结果，不会写 SimplyBook 或 Impact Key。

## 当前准备状态

仓库现已包含：

- 可运行的 Streamable HTTP MCP 后端：多维表快照读取、SimplyBook 只读工具、临时 Grant 和 Change Set 的受控演示流程。
- 只读 A2A 排期检查 Agent 和 AgentKit 编排 Agent 的部署配置。
- 容器构建与 AgentKit Runtime 部署脚本。

还没有任何云端 Runtime、MCP Gateway、飞书审批应用或客户后端连接。AgentKit CLI 需要先登录到有权限的火山引擎账号；当前工作会话未登录，因此本次没有创建云资源。

## 部署拓扑

| 组件 | 怎么部署 | 演示边界 |
|---|---|---|
| EMS MCP + 治理后端 | 构建容器并发布到 AgentKit MCP Gateway | 读取合成快照；SimplyBook 只读适配器默认 mock；没有 Agent 可调用的执行工具 |
| 排期检查 Agent | AgentKit Runtime | 独立只读 A2A Agent；编排 Agent 使用单独的 Runtime API Key 调用 |
| EMS 编排 Agent | AgentKit Runtime | 连接 MCP Gateway 和排期检查 Agent，生成预览并提交待审批 Change Set |
| Reviewer / Worker 路由 | 随后端容器提供 | 本地演示可用；云端审批回调/Worker 网络入口需要后续接入 Feishu 审批或客户指定的私有服务入口 |

此版本不会把 AgentKit Runtime 的调用 API Key 当作员工身份。Grant 中的 `demo.operator` 是服务端配置的合成身份。客户身份登录、Feishu 双审批、运行时用户身份传递、生产 Worker、SimplyBook 写入、Impact Key 同步和批量邮件都需要客户接口与租户配置，当前没有连接。

## 前置条件

1. 一个已开通 AgentKit 的火山引擎账号，以及 `default` AgentKit Project 的部署权限。
2. AgentKit CLI、Python 3.12、`uv`；构建并推送 MCP 镜像还需要 Docker Buildx 和一个可供 AgentKit 拉取镜像的 Container Registry 仓库。
3. 登录 Container Registry，并在本机 Docker 中完成一次 `docker login`。仓库地址、用户名和登录方式使用火山引擎控制台里该仓库的推送指引。
4. macOS/Linux shell。命令会在本地生成/使用 `.env`；这个文件被 Git 忽略。

AgentKit CLI 官方安装与 Runtime 部署说明见[官方 CLI 部署文档](https://docs.volcengine.com/docs/AgentKit/Creating_runtime_via_CLI_tool?lang=en)。MCP Gateway 的服务 URL、API Key 和 VeADK 接入方式见[官方 MCP 接入文档](https://docs.volcengine.com/docs/agentkit/Integrating_MCP_service_in_agent?lang=zh)。本仓库的 CLI 流程针对 AgentKit CLI 0.54.x 编写；如果 CLI 帮助有变化，以本机 `agentkit --help` 为准。

## A. 在本地跑 MCP 后端

```bash
git clone https://github.com/April-Xu/ems-agentkit-demo.git
cd ems-agentkit-demo
cp .env.example .env
```

在 `.env` 中为 Grant Reviewer、Change Set Reviewer 和 Worker 各填一个不同的随机值，仅用于本地演示。然后启动：

```bash
scripts/run-local-mcp.sh
```

新开一个终端检查服务：

```bash
curl http://127.0.0.1:8000/health
```

预期响应中有 `"status":"ok"`。MCP 地址是 `http://127.0.0.1:8000/mcp`。Reviewer 路由可查询待审批项：

```bash
curl http://127.0.0.1:8000/demo/reviewer/queue \
  -H "Authorization: Bearer $EMS_DEMO_GRANT_REVIEWER_KEY"
```

本地终端如未加载 `.env`，先执行 `set -a; source .env; set +a`。Reviewer 路由只模拟审批状态，不会创建飞书审批实例；Worker 路由只返回 `MOCK_ONLY_NOT_SENT`，不写任何客户系统。含特殊字符的 `.env` 值请使用 shell 引号；不要打开 shell 命令追踪（`set -x`）。

## B. 部署 MCP 后端并创建 MCP Gateway 服务

### 1. 登录火山引擎与镜像仓库

```bash
export PATH="$HOME/.local/bin:$PATH"
agentkit --version
agentkit login --console --provider volcengine
agentkit whoami
```

登录 Container Registry 后，在 `.env` 的 `EMS_MCP_IMAGE` 中填完整镜像地址，例如 `<你的仓库域名>/<命名空间>/ems-governance:demo-20260928`。然后构建并推送：

```bash
scripts/build-push-mcp.sh
```

### 2. 在 AgentKit MCP Gateway 建服务

下面的命令使用独立的演示镜像和 `cn-beijing` 区域。Gateway 为调用端启用 API Key；不要把 API Key 写入 repo。

```bash
set -a
source .env
set +a

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
  --inbound-api-key-name ems-agent
```

在 AgentKit 控制台打开 `ems-impact-week-demo` 服务详情，复制 MCP Endpoint 和入站 API Key 到 `.env` 的 `EMS_DEMO_MCP_URL`、`EMS_DEMO_MCP_AUTH_KEY`。URL 应是服务详情展示的完整 `/mcp` Endpoint。不要把这些值提交到 GitHub。

### 3. 确认服务能列出 MCP 工具

MCP 服务详情应显示可用状态。用 MCP Inspector 或 VeADK 客户端连 `EMS_DEMO_MCP_URL`，请求头设为 `Authorization: Bearer <EMS_DEMO_MCP_AUTH_KEY>`。确认工具列表中有 `list_events`、`simplybook_list_calendars`、`request_temporary_grant`、`prepare_change_set`、`freeze_change_set`、`submit_change_set_approval`；确认没有预订、取消、邮件发送或 Impact Key 写入工具。

## C. 部署两个 AgentKit Runtime

先部署排期检查 Agent：

```bash
scripts/deploy-agent.sh schedule-checker
```

在 AgentKit 控制台的 Runtime 详情中复制其 A2A Agent Card URL 和 Runtime API Key 到 `.env`：

- `EMS_SCHEDULE_CHECKER_AGENT_CARD_URL`：控制台显示的 Agent Card URL。
- `EMS_SCHEDULE_CHECKER_A2A_AUTH_KEY`：该 Runtime 的调用 API Key。
- `EMS_SCHEDULE_CHECKER_PUBLIC_URL`：该 Runtime 接收 A2A 请求的公开入口 URL。

然后再次部署排期检查 Agent，让其 Agent Card 使用真实的 Runtime 公网入口：

```bash
scripts/deploy-agent.sh schedule-checker
```

确认 Runtime Ready 后部署编排 Agent：

```bash
scripts/deploy-agent.sh orchestrator
```

验证 Runtime 状态并发起一次演示调用：

```bash
cd .deploy/orchestrator
agentkit status --config-file agentkit.yaml --verbose
agentkit invoke run --config-file agentkit.yaml \
  "读取 DEMO-IW-2026-001 和 BATCH-DEMO-001，检查重复、冲突和容量，申请临时 Grant，准备一个不超过 3 人的报名预览并提交待审批。不要执行写入。"
agentkit runtime logs ems-iw-demo-orchestrator --limit 100
```

部署脚本会先把 Agent 项目复制到被 Git 忽略的 `.deploy/` 目录，再从副本运行 CLI。AgentKit 会在配置副本里写入 Runtime ID、Endpoint 等部署状态；不要把 `.deploy/` 加入 Git。

演示时可展示 MCP 工具调用、A2A 排期检查、Grant 的 event/batch/action/expiry 范围，以及 Change Set 的冻结版本和 hash。当前 Grant 使用 `demo.operator` 合成主体，审批状态模拟，不代表员工 SSO 或真实 Feishu 审批。

## D. 本地模拟审批与 Worker 保护

本地运行 MCP 服务时，Grant Reviewer 和 Change Set Reviewer 使用两把不同的密钥。Agent 的 MCP 工具表不包含这些 HTTP 路由；Worker 另需独立的 `EMS_DEMO_WORKER_KEY`。模拟执行接口会二次检查 Grant、审批状态、版本/hash、过期时间和 Idempotency-Key，结果固定为 `SIMULATED`。

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

Feishu 审批回调和云端 Reviewer/Worker 私有入口尚未接入。不要把本地演示密钥复用为客户凭证，也不要将 Worker Key 配进 Agent Runtime。

## E. 回滚演示资源

```bash
agentkit runtime delete ems-iw-demo-orchestrator --yes --region cn-beijing
agentkit runtime delete ems-iw-demo-schedule-checker --yes --region cn-beijing
agentkit mcp service delete ems-impact-week-demo --yes --project default --region cn-beijing
```

同时在 Container Registry 删除这次 POC 使用的镜像版本。删除前确认资源名称与控制台中的演示资源一致。

## 部署后仍需客户提供/确认

- Feishu Base 的正式读取身份和 API 权限；当前镜像使用仓库内快照，Base 变更不会自动同步。
- 员工登录/身份令牌向 EMS 治理服务的可信传递方式，以及生产 Grant 策略。
- Feishu Grant/Change Set 审批定义、审批人、回调签名和云端 Reviewer 入口。
- SimplyBook 的可用环境、API 凭据及按人报名/取消/改期接口。现有 count-only 批量接口不能确认报名人与 booking 的绑定；当前写操作全部是 mock。
- Impact Key 的同步接口与幂等/回查方式；当前只展示 mock projection 状态。
- 云端私有 Worker 部署、数据库持久化、审计留存、任务重试和告警。
- 邮件发送接口及发送审批策略；当前 demo 不发送邮件。
