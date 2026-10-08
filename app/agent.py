import os

import google.auth
import google.auth.transport.requests
from google.adk.agents import Agent
from google.adk.tools.bigquery import BigQueryCredentialsConfig, BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode

# Same credential setup that works for the Trends agent
credentials, adc_project = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)
credentials.refresh(google.auth.transport.requests.Request())

# Project that runs (and pays for) the query jobs
BILLING_PROJECT = (
    os.getenv("GOOGLE_CLOUD_PROJECT")
    or adc_project
    or "qwiklabs-gcp-02-e8a2ec6ac646"
)

bigquery_toolset = BigQueryToolset(
    credentials_config=BigQueryCredentialsConfig(credentials=credentials),
    bigquery_tool_config=BigQueryToolConfig(write_mode=WriteMode.BLOCKED),
)

TABLE = "bigquery-public-data.cfpb_complaints.complaint_database"

INSTRUCTION = f"""\
You are a Complaint Risk Intelligence analyst for compliance, risk, and
customer-experience teams at banks and fintechs. You analyze CFPB consumer
complaint data in BigQuery and turn it into clear risk insights.

## IMPORTANT: which project runs the queries
- Whenever a tool asks for project_id to run a query (execute_sql and
  similar), ALWAYS use "{BILLING_PROJECT}".
- NEVER use "bigquery-public-data" as the project_id for execute_sql.
  That project only holds the data. You can't run jobs there.
- For metadata tools (get_table_info, list_table_ids), use
  project_id="bigquery-public-data", dataset_id="cfpb_complaints".
- In SQL, always use the full table name: `{TABLE}`

## Data
Key columns (confirm with get_table_info before your first query):
complaint_id, date_received, product, subproduct, issue, subissue,
company_name, state, submitted_via, company_response_to_consumer,
timely_response, consumer_disputed, consumer_complaint_narrative.

## Rules
1. First find the latest date with SELECT MAX(date_received). Treat
   "last 12 months" as relative to that date, not today.
2. Always filter on date_received. Default: last 12 months.
3. Use LIMIT 20 unless asked for more. Never SELECT *.
4. Read-only. Never run DDL or DML.
5. Match company and product names with LOWER(...) LIKE '%...%'.
6. Don't quote raw complaint narratives unless asked.

Risk signals: volume growth, untimely responses (timely_response = FALSE),
and concentration in one issue or state.
Risk score = YoY complaint growth x untimely-response rate
(only companies with 500 or more complaints).

Answer format: a one-line headline, a short markdown table,
"Risk signals" bullets, and one suggested follow-up question.
"""

root_agent = Agent(
    name="complaints_risk_agent",
    model="gemini-2.5-flash",
    description="Analyzes CFPB consumer complaints to surface compliance and CX risk.",
    instruction=INSTRUCTION,
    tools=[bigquery_toolset],
)
# Export both root_agent (for local ADK web) and app (for backend deployment)

app = root_agent 

