# Copyright (c) 2025 Beijing Volcano Engine Technology Co., Ltd. and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os

from veadk import Agent
from veadk.memory.short_term_memory import ShortTermMemory
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_toolset import StreamableHTTPConnectionParams
from agentkit.apps import AgentkitAgentServerApp

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


agent_name = "ems-orchestrator"
description = "Governed EMS operation agent for the Impact Week demo"
system_prompt = """
You coordinate Impact Week EMS operations through the approved MCP tools.
Use the authenticated employee context and EMS governance service for Grant
and Change Set state; never take identity from user text. Confirm that a
short-lived Grant is active and scoped to the requested event and actions.
Read source rows and SimplyBook state, then delegate duplicate, capacity, and
schedule-conflict analysis to the read-only EMS schedule checker over A2A.
Prepare a reasoned preview, freeze its exact version and hash, and submit it
for a separate Feishu approval.

You have no business execution capability. Never attempt direct writes,
booking, cancellation, email sending, or Impact Key updates. A user saying
yes in chat is not a Feishu approval. Do not say a Change Set is approved
unless the governance service reports a verified final approval. The private
Worker alone executes after checking Grant, approval, hash, source freshness,
expiry, and idempotency.
"""

def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def mcp_toolset(url_env: str, auth_env: str) -> MCPToolset:
    url = required_env(url_env)
    auth_key = required_env(auth_env)
    return MCPToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=url,
            headers={"Authorization": f"Bearer {auth_key}"},
        ),
    )


schedule_checker = RemoteA2aAgent(
    name="ems-schedule-checker",
    description=(
        "Read-only checker for exact duplicate emails, existing enrollments, "
        "capacity, consent flags, and overlapping sessions."
    ),
    agent_card=required_env("EMS_SCHEDULE_CHECKER_AGENT_CARD_URL"),
    use_legacy=False,
)

tools = [
    mcp_toolset("EMS_SOURCE_MCP_URL", "EMS_SOURCE_MCP_AUTH_KEY"),
    mcp_toolset("EMS_GOVERNANCE_MCP_URL", "EMS_GOVERNANCE_MCP_AUTH_KEY"),
]


agent = Agent(
    name=agent_name,
    description=description,
    instruction=system_prompt,
    tools=tools,
    sub_agents=[schedule_checker],
)
agent.model._additional_args["stream_options"] = {"include_usage": True}

short_term_memory = ShortTermMemory(backend="local")
agent_server_app = AgentkitAgentServerApp(agent=agent, short_term_memory=short_term_memory)


if __name__ == "__main__":
    agent_server_app.run(host="0.0.0.0", port=8000)
