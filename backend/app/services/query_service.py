import time
from typing import Optional
import pandas as pd

from app.database import query_data, get_data_sources, get_data_source, save_query_history, get_context_for_source
from app.services.claude_service import ClaudeService
from app.services.marketing_intelligence import MarketingIntelligence
from app.services.advanced_analytics import AdvancedAnalytics
from app.services.conversion_analytics import ConversionAnalytics
from app.services.incrementality import IncrementalityAnalyzer


class QueryService:
    """Service for handling natural language queries against data sources."""

    def __init__(self):
        self.claude = ClaudeService()
        self.marketing_intel = MarketingIntelligence()
        self.analytics = AdvancedAnalytics()
        self.conversion = ConversionAnalytics()
        self.incrementality = IncrementalityAnalyzer()

    def process_query(self, question: str, data_source_ids: Optional[list[str]] = None,
                     deep_analysis: bool = True) -> dict:
        """
        Process a natural language query.

        1. Get relevant data sources and their schemas
        2. Generate SQL using Claude
        3. Execute the query
        4. Run advanced analytics
        5. Generate deep marketing insights
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

        # Get advertiser context (use first source's context, or global)
        advertiser_context = None
        if sources:
            advertiser_context = get_context_for_source(sources[0]["id"])

        # Generate SQL query
        sql_result = self.claude.generate_sql(question, schema_info, table_names, advertiser_context)
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

        # Initialize result containers
        insights_result = {}
        advanced_analysis = {}

        # Run analysis if we have data
        if data and not error:
            combined_schema = {"columns": [col for s in schema_info for col in s.get("columns", [])]}
            df = pd.DataFrame(data)

            # Run advanced analytics in parallel
            advanced_analysis = self._run_advanced_analytics(df, question)

            if deep_analysis:
                # Get deep marketing intelligence
                insights_result = self.marketing_intel.analyze_performance(
                    data, combined_schema, question, advertiser_context
                )
            else:
                # Fallback to basic insights
                insights_result = self.claude.generate_insights(question, data, combined_schema, advertiser_context)

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

            # Deep marketing intelligence
            "executive_summary": insights_result.get("executive_summary", ""),
            "performance_assessment": insights_result.get("performance_assessment", {}),
            "deep_insights": insights_result.get("deep_insights", []),
            "funnel_analysis": insights_result.get("funnel_analysis", {}),
            "channel_analysis": insights_result.get("channel_analysis", []),
            "budget_recommendations": insights_result.get("budget_recommendations", {}),
            "anomalies_detected": insights_result.get("anomalies_detected", []),
            "strategic_recommendations": insights_result.get("strategic_recommendations", []),
            "testing_suggestions": insights_result.get("testing_suggestions", []),

            # Legacy fields for compatibility
            "insights": insights_result.get("executive_summary") or insights_result.get("insights", ""),
            "key_findings": [i.get("insight", i.get("title", "")) for i in insights_result.get("deep_insights", [])][:5],
            "recommendations": [r.get("recommendation", r) for r in insights_result.get("strategic_recommendations", [])][:5],

            # Advanced analytics
            "analytics": advanced_analysis,

            # Visualization and follow-up
            "visualization": insights_result.get("visualization") or self._suggest_visualization(data, question),
            "follow_up_questions": insights_result.get("follow_up_questions", []),
            "data_quality_notes": insights_result.get("data_quality_notes", []),

            # Metadata
            "execution_time_ms": execution_time_ms,
            "row_count": len(data),
            "analysis_depth": "deep" if deep_analysis else "basic"
        }

    def _run_advanced_analytics(self, df: pd.DataFrame, question: str) -> dict:
        """Run advanced analytics on the data."""
        analytics_results = {}
        question_lower = question.lower()

        try:
            # Time series analysis
            if 'date' in df.columns:
                metric_cols = [c for c in df.columns if c in ['spend', 'revenue', 'conversions', 'clicks', 'impressions']]
                if metric_cols:
                    analytics_results["time_series"] = self.analytics.analyze_time_series(
                        df, metric_cols[0], 'date'
                    )

                    # Anomaly detection
                    analytics_results["anomalies"] = self.analytics.detect_anomalies(
                        df, metric_cols[0], 'date'
                    )

            # Attribution analysis
            if 'channel' in df.columns or 'source' in df.columns:
                analytics_results["attribution"] = self.analytics.attribution_analysis(df)

            # Correlation analysis
            analytics_results["correlations"] = self.analytics.correlation_analysis(df)

            # Segmentation
            for dim in ['channel', 'campaign', 'source']:
                if dim in df.columns:
                    analytics_results[f"segmentation_by_{dim}"] = self.analytics.segmentation_analysis(df, dim)
                    break

            # Conversion funnel analysis
            if 'clicks' in df.columns and 'conversions' in df.columns:
                analytics_results["conversion_funnel"] = self.conversion.analyze_conversion_funnel(df)

                # Conversion rate by segment (if relevant dimensions exist)
                for dim in ['channel', 'campaign', 'source']:
                    if dim in df.columns:
                        analytics_results[f"conversion_by_{dim}"] = self.conversion.conversion_rate_by_segment(df, dim)
                        break

                # Conversion trends if date available
                if 'date' in df.columns:
                    analytics_results["conversion_trends"] = self.conversion.conversion_trend_analysis(df)

            # Incrementality analysis (if question relates to it or we have spend/conversion data)
            incrementality_keywords = ['incremental', 'incrementality', 'true impact', 'causal', 'lift', 'holdout']
            has_required_data = 'spend' in df.columns and 'conversions' in df.columns
            question_asks_incrementality = any(kw in question_lower for kw in incrementality_keywords)

            if has_required_data and ('channel' in df.columns or 'source' in df.columns):
                # Always run basic incrementality estimation
                analytics_results["incrementality"] = self.incrementality.estimate_channel_incrementality(df)

                # Time-based incrementality if we have dates
                if 'date' in df.columns:
                    analytics_results["time_based_incrementality"] = self.incrementality.time_based_incrementality(df)

        except Exception as e:
            analytics_results["error"] = str(e)

        return analytics_results

    def _suggest_visualization(self, data: list[dict], question: str) -> dict:
        """Suggest appropriate visualization based on data and question."""
        if not data:
            return {"type": "table", "title": "No Data"}

        df = pd.DataFrame(data)
        columns = list(df.columns)
        question_lower = question.lower()

        # Determine visualization type based on question and data
        if any(word in question_lower for word in ['trend', 'over time', 'daily', 'weekly', 'monthly']):
            date_col = next((c for c in columns if 'date' in c.lower()), columns[0])
            metric_col = next((c for c in columns if c not in [date_col] and df[c].dtype in ['int64', 'float64']), None)
            return {
                "type": "line",
                "title": f"{metric_col} Over Time" if metric_col else "Trend",
                "x_axis": date_col,
                "y_axis": metric_col
            }

        elif any(word in question_lower for word in ['breakdown', 'by', 'compare', 'comparison']):
            # Look for a categorical and numeric column
            cat_col = next((c for c in columns if df[c].dtype == 'object'), columns[0])
            num_col = next((c for c in columns if c != cat_col and df[c].dtype in ['int64', 'float64']), None)

            if len(df) <= 6:
                return {
                    "type": "pie",
                    "title": f"{num_col} by {cat_col}" if num_col else "Distribution",
                    "x_axis": cat_col,
                    "y_axis": num_col
                }
            return {
                "type": "bar",
                "title": f"{num_col} by {cat_col}" if num_col else "Comparison",
                "x_axis": cat_col,
                "y_axis": num_col
            }

        elif any(word in question_lower for word in ['total', 'sum', 'overall']):
            if len(data) == 1:
                return {
                    "type": "metric",
                    "title": "Total",
                    "x_axis": None,
                    "y_axis": list(data[0].keys())[0]
                }

        elif any(word in question_lower for word in ['correlation', 'relationship', 'vs', 'versus']):
            numeric_cols = [c for c in columns if df[c].dtype in ['int64', 'float64']]
            if len(numeric_cols) >= 2:
                return {
                    "type": "scatter",
                    "title": f"{numeric_cols[0]} vs {numeric_cols[1]}",
                    "x_axis": numeric_cols[0],
                    "y_axis": numeric_cols[1]
                }

        # Default: bar chart or table
        if len(df) <= 20:
            cat_col = next((c for c in columns if df[c].dtype == 'object'), columns[0])
            num_col = next((c for c in columns if c != cat_col and df[c].dtype in ['int64', 'float64']), None)
            return {
                "type": "bar",
                "title": "Results",
                "x_axis": cat_col,
                "y_axis": num_col
            }

        return {"type": "table", "title": "Query Results"}

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
