import os
import google.auth
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.tools.bigquery import BigQueryCredentialsConfig, BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode

# 1. Fetch credentials
credentials, default_project = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

# 2. Configure BigQuery Toolset
tool_config = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)
bigquery_toolset = BigQueryToolset(
    credentials_config=BigQueryCredentialsConfig(credentials=credentials),
    bigquery_tool_config=tool_config,
)

TABLE = "bigquery-public-data.cfpb_complaints.complaint_database"
BILLING_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT") or default_project or "qwiklabs-gcp-02-e8a2ec6ac646"

INSTRUCTION = f"""\
You are a Complaint Risk Intelligence analyst for compliance, risk, and customer-experience teams at banks and fintechs.
You analyze CFPB consumer complaint data in BigQuery and turn it into clear risk insights.

Table: `{TABLE}`
Always run queries using the billing project `{BILLING_PROJECT}`.

Rules:
1. First find the latest date using SELECT MAX(date_received) FROM `{TABLE}`. Treat "last 12 months" relative to that date.
2. Always filter on date_received to minimize scan volume.
3. Default to LIMIT 20 unless the user requests more. Never execute SELECT *.
4. Read-only access: never execute DDL or DML statements.
5. Match names case-insensitively using LOWER(company_name) LIKE '%...%'.
6. Do not quote raw complaint narratives unless explicitly asked.

Answer format:
1. Headline finding (1 line).
2. Key metrics in a markdown table.
3. Risk signals bullet points.
4. One recommended follow-up question.
"""

# 3. Define root_agent
root_agent = Agent(
    name="complaints_risk_agent",
    model="gemini-2.5-flash",
    description="Analyzes CFPB consumer complaints to surface compliance and CX risk.",
    instruction=INSTRUCTION,
    tools=[bigquery_toolset],
)

# 4. Wrap root_agent in App for backend deployment
app = App(
    root_agent=root_agent,
    name="app",
)

