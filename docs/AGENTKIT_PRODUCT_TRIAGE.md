# AgentKit 产品问题初筛

更新时间：2026-09-30。本文把 demo 部署过程中遇到的异常与 AgentKit 产品问题分开记录。当前 CLI 的火山引擎登录已过期，因此云端复现暂时没有重新执行；下文明确标出已验证事实与待产品确认项。

## 初筛结论

目前**没有足够证据确认 AgentKit 存在已确定的产品缺陷**。有一项值得交给 AgentKit 产品团队确认：Runtime 显示 `Ready` 时，模型调用仍可能因为模型不可用或账号无权限而失败。它也可能是正常的状态定义——`Ready` 只代表容器/服务启动，而不代表下游模型依赖可用。

## 候选产品问题

### AK-CANDIDATE-01：Runtime `Ready` 与模型可调用状态不一致

| 项目 | 记录 |
|---|---|
| 分类 | AgentKit Runtime 产品体验候选；**未确认是缺陷** |
| 影响 | 用户可能把 `Ready` 理解为 Agent 可正常应答，实际首次调用才发现模型不可用/无权限 |
| 复现证据 | 2026-09-29 的云端部署检查中，Runtime 状态为 `Ready`；A2A 调用返回 `The model or endpoint doubao-seed-1-8-251228 does not exist or you do not have access to it.` |
| 后续验证 | 显式配置账号可调用的 `MODEL_AGENT_NAME` 与 `MODEL_ENDPOINT` 后，Runtime 调用成功；说明直接阻断原因是模型配置或账号权限，不足以证明 AgentKit 缺陷 |
| 建议产品确认 | `Ready` 的定义是否只覆盖进程健康？是否可以在控制台区分“服务已启动”和“依赖/模型可调用”，或在部署前提供一次模型权限检查？ |
| 置信度 | 现象高；AgentKit 责任低至中，待产品团队确认状态语义 |

**复现步骤（仅在隔离测试 Runtime 上执行）**

1. 在测试账号中选择一个该账号未开通的模型，部署一个临时 Runtime；不要修改当前 demo Runtime。
2. 等待控制台显示 `Ready`，记录 Runtime 状态。
3. 对该 Runtime 发起一次 A2A/Agent 调用。
4. 对比：Runtime 仍显示 `Ready`，但调用以模型不存在或无访问权限的错误失败。
5. 换成已开通模型并配置 `MODEL_AGENT_NAME`、`MODEL_ENDPOINT` 后重新部署；确认调用恢复。

复现依赖“账号确实没有所选模型权限”。若测试账号有权限，该现象不会复现。

![Runtime Ready 但模型调用失败的脱敏复现记录](evidence/agentkit/runtime-ready-model-call-failure.png)

图为根据 2026-09-29 已观察到的 CLI 输出整理的脱敏证据图，不是原始控制台截图；现有会话过期后未重新抓取云端画面。

## 产品能力/架构确认项（不按缺陷登记）

### AK-CAPABILITY-01：MCP Gateway 的服务路由边界

当前 demo 将 Gateway 配置为 MCP `/mcp` 入口。Reviewer 与 Worker 的 HTTP 路由仅在本地后端运行，公网 Gateway 未发布这些路由；云端因此不能通过本地 Reviewer API 继续共享状态的审批和执行流程。这是 demo 的部署/架构边界，**当前没有证据表明它是 AgentKit 缺陷**。

客户如果需要云端 Reviewer/Worker，需先确认 AgentKit 是否支持将多个 HTTP 路由发布到同一个 Gateway，或应为治理 API 单独部署服务/网关，并通过持久化共享状态衔接。不要把当前本地审批描述成飞书原生审批。

## 已归为 demo / 配置 / 依赖问题

| 现象 | 归属判断 | 依据/处理 |
|---|---|---|
| 首次编排 Agent 云构建因 `google.adk.a2a.executor.config` 不存在而失败 | Google ADK 依赖版本兼容，不是 AgentKit 已确认问题 | 将 `google-adk[a2a]` 限定在 `>=1.34,<2.0` 后部署成功；参见 [部署指南](DEPLOYMENT.md) |
| MCP Gateway 返回 `421 Invalid Host header` | Demo MCP 后端 Host allowlist 配置 | 加入 Gateway 的精确主机名并重启后恢复；不是 AgentKit 产品问题 |
| 当前云端 Grant 停在 `PENDING_APPROVAL`，Reviewer/Worker 无法续跑 | demo 路由与状态存储尚未打通 | Gateway 只暴露 `/mcp`；本地 Reviewer/Worker 使用独立 SQLite；需补云端审批 API 与共享持久化 |
| 飞书多维表实时读取、原生审批、SimplyBook 写入、Impact Key 同步和邮件发送未接入 | demo 集成范围 | 当前数据是合成快照，SimplyBook/Worker 为 mock；不属于 AgentKit 产品缺陷 |
| A2A 输出有较多过程性文本 | Agent 指令/模型输出行为，尚未验证改 prompt 后云端效果 | 已在本地 prompt 加入简洁输出约束，但未重新部署验证；不归因于 AgentKit |
| 本机 AgentKit CLI 登录会话过期 | 短时 SSO 凭证生命周期/本机认证状态 | 2026-09-30 的 `whoami` 显示会话已于 2026-09-29 到期；这是本次无法重新截取云端画面的原因，暂不登记为产品问题 |

## 提交产品团队前建议补齐

- 用隔离 Runtime 复现 `Ready` 与模型调用失败，并截取同一时刻的控制台状态与调用错误。
- 记录 AgentKit CLI、Runtime SDK/镜像版本、区域和 Runtime 状态时间；不要公开账号 ID、API Key、STS 或请求签名。
- 请产品团队先确认 `Ready` 的产品定义，再决定是否登记为缺陷或增强需求。
