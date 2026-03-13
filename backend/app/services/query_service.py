import time
from typing import Optional

from app.database import query_data, get_data_sources, get_data_source, save_query_history
from app.services.claude_service import ClaudeService


class QueryService:
    """Service for handling natural language queries against data sources."""

    def __init__(self):
        self.claude = ClaudeService()

    def process_query(self, question: str, data_source_ids: Optional[list[str]] = None) -> dict:
        """
        Process a natural language query.

        1. Get relevant data sources and their schemas
        2. Generate SQL using Claude
        3. Execute the query
        4. Generate insights and visualization recommendations
        """
        start_time = time.time()

        # Get data sources
        if data_source_ids:
            sources = [get_data_source(sid) for sid in data_source_ids if get_data_source(sid)]
        else:
            sources = get_data_sources()

        if not sources:
            return {
                "question": question,
                "error": "No data sources available. Please upload a CSV or connect a Google Sheet first.",
                "sql_query": None,
                "data": [],
                "insights": None,
                "recommendations": [],
                "visualization": None,
                "execution_time_ms": 0
            }

        # Prepare schema info and table names
        schema_info = [s.get("schema_info", {}) for s in sources]
        table_names = [s["config"]["table_name"] for s in sources]

        # Generate SQL query
        sql_result = self.claude.generate_sql(question, schema_info, table_names)
        sql_query = sql_result.get("sql", "")

        # Execute the query
        try:
            df = query_data(sql_query)
            data = df.to_dict(orient="records")
            error = None
        except Exception as e:
            data = []
            error = str(e)

            # Try to fix the SQL if it failed
            if error:
                fixed_sql = self._attempt_sql_fix(question, sql_query, error, schema_info, table_names)
                if fixed_sql:
                    try:
                        df = query_data(fixed_sql)
                        data = df.to_dict(orient="records")
                        sql_query = fixed_sql
                        error = None
                    except Exception as e2:
                        error = f"Original error: {error}. Retry error: {str(e2)}"

        # Generate insights if we have data
        insights_result = {}
        if data and not error:
            combined_schema = {"columns": [col for s in schema_info for col in s.get("columns", [])]}
            insights_result = self.claude.generate_insights(question, data, combined_schema)

        # Save to history
        result_summary = f"{len(data)} rows returned" if data else error or "No results"
        save_query_history(question, sql_query, result_summary)

        execution_time_ms = int((time.time() - start_time) * 1000)

        return {
            "question": question,
            "sql_query": sql_query,
            "sql_explanation": sql_result.get("explanation", ""),
            "data": data,
            "error": error,
            "insights": insights_result.get("insights", ""),
            "key_findings": insights_result.get("key_findings", []),
            "recommendations": insights_result.get("recommendations", []),
            "visualization": insights_result.get("visualization"),
            "follow_up_questions": insights_result.get("follow_up_questions", []),
            "execution_time_ms": execution_time_ms,
            "row_count": len(data)
        }

    def _attempt_sql_fix(
        self,
        question: str,
        failed_sql: str,
        error: str,
        schema_info: list,
        table_names: list[str]
    ) -> Optional[str]:
        """Attempt to fix a failed SQL query."""
        schema_description = self.claude._format_schema_for_prompt(schema_info, table_names)

        prompt = f"""The following SQL query failed. Please fix it.

ORIGINAL QUESTION: {question}

FAILED SQL:
{failed_sql}

ERROR MESSAGE:
{error}

DATABASE SCHEMA:
{schema_description}

Respond with ONLY the corrected SQL query, no explanation."""

        response = self.claude.client.messages.create(
            model=self.claude.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        fixed_sql = response.content[0].text.strip()

        # Clean up the response (remove markdown code blocks if present)
        if fixed_sql.startswith("```"):
            lines = fixed_sql.split("\n")
            fixed_sql = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        return fixed_sql if fixed_sql else None
