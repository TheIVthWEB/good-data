import json
from typing import Optional
import anthropic

from app.config import settings


class ClaudeService:
    """Service for Claude API interactions - NL to SQL, insights, and recommendations."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model

    def _format_advertiser_context(self, context: Optional[dict]) -> str:
        """Format advertiser context for inclusion in prompts."""
        if not context:
            return ""

        lines = ["\n\nADVERTISER CONTEXT:"]

        if context.get("name"):
            lines.append(f"Client: {context['name']}")

        if context.get("industry"):
            lines.append(f"Industry: {context['industry']}")

        if context.get("business_model"):
            lines.append(f"Business Model: {context['business_model']}")

        if context.get("sales_cycle_days"):
            lines.append(f"Sales Cycle: {context['sales_cycle_days']} days")

        if context.get("primary_kpi"):
            lines.append(f"Primary KPI: {context['primary_kpi']}")

        if context.get("secondary_kpis"):
            lines.append(f"Secondary KPIs: {', '.join(context['secondary_kpis'])}")

        # Targets
        targets = []
        if context.get("target_cpa"):
            targets.append(f"CPA < ${context['target_cpa']}")
        if context.get("target_roas"):
            targets.append(f"ROAS > {context['target_roas']}x")
        if context.get("target_ctr"):
            targets.append(f"CTR > {context['target_ctr']}%")
        if targets:
            lines.append(f"Targets: {', '.join(targets)}")

        # Industry benchmarks
        if context.get("industry_benchmarks"):
            benchmarks = context["industry_benchmarks"]
            bench_str = ", ".join([f"{k}: {v}" for k, v in benchmarks.items()])
            lines.append(f"Industry Benchmarks: {bench_str}")

        # Channel rules
        if context.get("channel_rules"):
            lines.append("\nChannel-Specific Rules:")
            for rule in context["channel_rules"]:
                lines.append(f"  - {rule.get('channel', 'Unknown')}: {rule.get('rule', '')}")

        # Attribution preferences
        if context.get("attribution_window_days"):
            lines.append(f"\nAttribution Window: {context['attribution_window_days']} days")
        if context.get("preferred_attribution_model"):
            lines.append(f"Preferred Attribution Model: {context['preferred_attribution_model']}")

        # Do's and Don'ts
        if context.get("dos"):
            lines.append("\nDO:")
            for do in context["dos"]:
                lines.append(f"  - {do}")

        if context.get("donts"):
            lines.append("\nDO NOT:")
            for dont in context["donts"]:
                lines.append(f"  - {dont}")

        # Custom instructions
        if context.get("custom_instructions"):
            lines.append(f"\nAdditional Instructions:\n{context['custom_instructions']}")

        return "\n".join(lines)

    def generate_sql(self, question: str, schema_info: dict, table_names: list[str],
                     advertiser_context: Optional[dict] = None) -> dict:
        """
        Convert natural language question to SQL query.

        Returns dict with 'sql' and 'explanation' keys.
        """
        schema_description = self._format_schema_for_prompt(schema_info, table_names)

        prompt = f"""You are a SQL expert helping analyze marketing and advertising data.
Convert the following natural language question into a SQL query.

DATABASE SCHEMA:
{schema_description}

QUESTION: {question}

IMPORTANT GUIDELINES:
- Use SQLite syntax
- Always use table names exactly as provided
- For date operations, use SQLite date functions
- Round monetary values to 2 decimal places
- Calculate derived metrics when relevant (CTR, CPC, CPA, ROAS, etc.)
- CTR = clicks / impressions * 100
- CPC = spend / clicks
- CPA = spend / conversions
- ROAS = revenue / spend
- CPM = spend / impressions * 1000
{self._format_advertiser_context(advertiser_context)}

Respond in JSON format:
{{
    "sql": "YOUR SQL QUERY HERE",
    "explanation": "Brief explanation of what the query does",
    "metrics_calculated": ["list of any calculated metrics"]
}}"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse the response
        response_text = response.content[0].text
        try:
            # Try to extract JSON from the response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response_text[json_start:json_end])
        except json.JSONDecodeError:
            pass

        # Fallback if JSON parsing fails
        return {
            "sql": response_text,
            "explanation": "Generated SQL query",
            "metrics_calculated": []
        }

    def generate_insights(self, question: str, data: list[dict], schema_info: dict,
                          advertiser_context: Optional[dict] = None) -> dict:
        """
        Generate insights and recommendations from query results.

        Returns dict with 'insights', 'recommendations', and 'visualization' keys.
        """
        # Limit data size for prompt
        sample_data = data[:50] if len(data) > 50 else data
        data_summary = f"Total rows: {len(data)}, Sample shown: {len(sample_data)}"

        prompt = f"""You are a marketing analytics expert analyzing campaign and advertising data.

ORIGINAL QUESTION: {question}

DATA SUMMARY: {data_summary}

DATA SAMPLE:
{json.dumps(sample_data, indent=2, default=str)}

COLUMN INFORMATION:
{json.dumps(schema_info.get('columns', []), indent=2)}

Analyze this data and provide:
1. Key insights (what does the data tell us?)
2. Actionable recommendations for improving marketing performance
3. Suggested visualization type and configuration

Consider these marketing aspects:
- Campaign performance trends
- Cost efficiency (CPC, CPA, CPM)
- Return on investment (ROAS)
- Channel/source attribution
- Audience segment performance
- Temporal patterns (day of week, time of day, seasonality)
- Budget allocation optimization
{self._format_advertiser_context(advertiser_context)}

IMPORTANT: If advertiser context is provided above, you MUST follow the do's and don'ts exactly.
Compare metrics against the provided targets and benchmarks when making recommendations.

Respond in JSON format:
{{
    "insights": "Detailed narrative insights about the data (2-3 paragraphs)",
    "key_findings": [
        "Finding 1",
        "Finding 2",
        "Finding 3"
    ],
    "recommendations": [
        "Specific actionable recommendation 1",
        "Specific actionable recommendation 2",
        "Specific actionable recommendation 3"
    ],
    "visualization": {{
        "type": "bar|line|pie|scatter|table|metric|funnel|heatmap",
        "title": "Chart title",
        "x_axis": "column name for x-axis (if applicable)",
        "y_axis": "column name for y-axis (if applicable)",
        "rationale": "Why this visualization type is best"
    }},
    "follow_up_questions": [
        "Suggested follow-up question 1",
        "Suggested follow-up question 2"
    ]
}}"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text
        try:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response_text[json_start:json_end])
        except json.JSONDecodeError:
            pass

        return {
            "insights": response_text,
            "key_findings": [],
            "recommendations": [],
            "visualization": {"type": "table", "title": "Query Results"},
            "follow_up_questions": []
        }

    def suggest_visualization(self, data: list[dict], question: str) -> dict:
        """
        Suggest the best visualization type for the data.
        """
        if not data:
            return {"type": "table", "title": "No Data"}

        sample = data[0]
        columns = list(sample.keys())
        row_count = len(data)

        prompt = f"""Given this data structure, suggest the best visualization:

COLUMNS: {columns}
ROW COUNT: {row_count}
SAMPLE ROW: {json.dumps(sample, default=str)}
QUESTION CONTEXT: {question}

Respond in JSON:
{{
    "type": "bar|line|pie|scatter|table|metric|funnel|heatmap",
    "x_axis": "column name or null",
    "y_axis": "column name or null",
    "title": "suggested title",
    "config": {{}}
}}"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text
        try:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response_text[json_start:json_end])
        except json.JSONDecodeError:
            pass

        return {"type": "table", "title": "Query Results"}

    def _format_schema_for_prompt(self, schema_info: dict, table_names: list[str]) -> str:
        """Format schema info for inclusion in prompts."""
        lines = []
        for i, table_name in enumerate(table_names):
            lines.append(f"TABLE: {table_name}")
            if isinstance(schema_info, list):
                columns = schema_info[i].get("columns", []) if i < len(schema_info) else []
            else:
                columns = schema_info.get("columns", [])

            for col in columns:
                semantic = f" [{col.get('semantic_type', '')}]" if col.get('semantic_type') else ""
                lines.append(f"  - {col['name']} ({col['dtype']}){semantic}")
            lines.append("")

        return "\n".join(lines)
