import logging
import os

from agentkit.apps import AgentkitAgentServerApp
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_toolset import StreamableHTTPConnectionParams
from veadk import Agent
from veadk.memory.short_term_memory import ShortTermMemory

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


base_read_toolset = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=required_env("EMS_AUDITOR_MCP_URL"),
        headers={
            "Authorization": (
                f"Bearer {required_env('EMS_AUDITOR_MCP_AUTH_KEY')}"
            )
        },
    ),
)

agent = Agent(
    name="ems-data-auditor",
    description="Scheduled read-only EMS data quality review",
    instruction="""
You perform a read-only review of the explicitly requested Feishu Base table.
Find exact duplicate emails, likely duplicate participant rows, missing or
invalid required fields, inconsistent dates, and translation candidates.
Return a review report with source table/record identifiers, evidence, and
suggested corrections or English/Chinese translations.

Do not update or delete Base records, change consent, enroll or remove
participants, send email, create approvals, or call write tools. Mark
ambiguous findings as needing a human decision. The source MCP service is
read-only and should contain no mutation methods.
""",
    tools=[base_read_toolset],
)

memory = ShortTermMemory(backend="local")
app = AgentkitAgentServerApp(agent=agent, short_term_memory=memory)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8002")))

