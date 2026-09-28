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

from veadk import Agent, Runner
from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor
from agentkit.apps import AgentkitA2aApp

logger = logging.getLogger(__name__)

a2a_app = AgentkitA2aApp()

agent_name = "ems-schedule-checker"
description = "Read-only duplicate, capacity, and schedule conflict checker for EMS demo"
system_prompt = """
You are a read-only EMS schedule and data quality specialist. Analyze only
the source data included in the A2A request. Return concise, structured
findings for exact duplicate emails, existing enrollments, schedule overlaps,
consent flags, and remaining capacity. For every finding, include source
record identifiers, the observed values, a reason, and whether the row is
included, skipped, held, or requires human confirmation.

Do not resolve ambiguous identity, infer consent, move a person to another
session, grant authorization, approve a Change Set, edit data, enroll people,
or call write tools. The orchestrator and governance service decide what to
prepare; a human reviewer decides whether to approve.
"""


tools = []

# from veadk.tools.builtin_tools.web_search import web_search
# tools.append(web_search)


agent = Agent(
    name=agent_name,
    description=description,
    instruction=system_prompt,
    tools=tools,
)
runner = Runner(agent=agent)

@a2a_app.agent_executor(runner=runner)
class MyAgentExecutor(A2aAgentExecutor):
    pass

@a2a_app.ping
def ping() -> str:
    return "pong!"

if __name__ == "__main__":
    public_url = os.getenv(
        "EMS_SCHEDULE_CHECKER_PUBLIC_URL",
        "http://localhost:8001",
    )
    port = int(os.getenv("PORT", "8001"))
    from a2a.types import AgentCard, AgentProvider, AgentSkill, AgentCapabilities
    
    agent_card = AgentCard(
        capabilities=AgentCapabilities(streaming=True),
        description=agent.description,
        name=agent.name,
        default_input_modes=["text"],
        default_output_modes=["text"],
        provider=AgentProvider(organization="veadk", url=""),
        skills=[AgentSkill(id="0", name="chat", description="Chat", tags=["chat"])],
        url=public_url,
        version="1.0.0",
    )
    
    a2a_app.run(
        agent_card=agent_card,
        host="0.0.0.0",
        port=port,
    )
