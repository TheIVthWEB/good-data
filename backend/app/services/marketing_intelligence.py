"""
Marketing Intelligence Service

Deep marketing analytics powered by Claude with:
- Industry benchmarks and best practices
- Marketing frameworks (funnel analysis, attribution, etc.)
- Strategic recommendations based on data patterns
- Anomaly detection and trend analysis
- Budget optimization suggestions
- Competitive positioning insights
"""

import json
from typing import Optional
import anthropic

from app.config import settings


# Industry benchmarks by channel (approximate averages)
INDUSTRY_BENCHMARKS = {
    "google_ads": {
        "ctr": {"low": 1.5, "avg": 3.17, "high": 6.0, "unit": "%"},
        "cpc": {"low": 0.5, "avg": 2.69, "high": 5.0, "unit": "$"},
        "conversion_rate": {"low": 1.0, "avg": 3.75, "high": 8.0, "unit": "%"},
        "cpa": {"low": 20, "avg": 48.96, "high": 100, "unit": "$"},
    },
    "facebook": {
        "ctr": {"low": 0.5, "avg": 0.90, "high": 2.0, "unit": "%"},
        "cpc": {"low": 0.3, "avg": 1.72, "high": 3.0, "unit": "$"},
        "conversion_rate": {"low": 2.0, "avg": 9.21, "high": 15.0, "unit": "%"},
        "cpm": {"low": 5, "avg": 11.54, "high": 20, "unit": "$"},
    },
    "instagram": {
        "ctr": {"low": 0.3, "avg": 0.58, "high": 1.5, "unit": "%"},
        "cpc": {"low": 0.4, "avg": 1.28, "high": 2.5, "unit": "$"},
        "engagement_rate": {"low": 1.0, "avg": 1.94, "high": 4.0, "unit": "%"},
    },
    "linkedin": {
        "ctr": {"low": 0.3, "avg": 0.44, "high": 1.0, "unit": "%"},
        "cpc": {"low": 3.0, "avg": 5.58, "high": 10.0, "unit": "$"},
        "conversion_rate": {"low": 2.0, "avg": 6.1, "high": 12.0, "unit": "%"},
    },
    "tiktok": {
        "ctr": {"low": 0.5, "avg": 1.0, "high": 3.0, "unit": "%"},
        "cpm": {"low": 5, "avg": 10, "high": 20, "unit": "$"},
        "engagement_rate": {"low": 3.0, "avg": 5.96, "high": 10.0, "unit": "%"},
    },
    "email": {
        "open_rate": {"low": 15, "avg": 21.5, "high": 35, "unit": "%"},
        "ctr": {"low": 1.5, "avg": 2.62, "high": 5.0, "unit": "%"},
        "conversion_rate": {"low": 1.0, "avg": 2.5, "high": 6.0, "unit": "%"},
    },
}

# ROAS benchmarks by industry
ROAS_BENCHMARKS = {
    "ecommerce": {"min_acceptable": 3.0, "good": 4.0, "excellent": 6.0},
    "saas": {"min_acceptable": 2.0, "good": 3.0, "excellent": 5.0},
    "lead_gen": {"min_acceptable": 1.5, "good": 2.5, "excellent": 4.0},
    "brand_awareness": {"min_acceptable": 0.5, "good": 1.0, "excellent": 2.0},
}

MARKETING_SYSTEM_PROMPT = """You are an expert marketing analyst and strategist with deep knowledge of:

1. **Performance Marketing**
   - Paid search (Google Ads, Bing)
   - Paid social (Meta, TikTok, LinkedIn, Twitter)
   - Programmatic display and video
   - Affiliate and influencer marketing

2. **Marketing Frameworks**
   - AIDA (Attention, Interest, Desire, Action)
   - Marketing funnel analysis (TOFU, MOFU, BOFU)
   - Customer journey mapping
   - Attribution modeling (first-touch, last-touch, multi-touch, data-driven)
   - Media mix modeling
   - Incrementality testing

3. **Key Metrics & KPIs**
   - Efficiency metrics: CPC, CPM, CPA, CAC
   - Performance metrics: CTR, conversion rate, ROAS, LTV
   - Engagement metrics: time on site, bounce rate, pages per session
   - Brand metrics: reach, frequency, brand lift

4. **Industry Benchmarks**
   - You know typical performance ranges by channel and industry
   - You can identify when metrics are above or below expectations
   - You understand seasonality patterns

5. **Strategic Thinking**
   - Budget allocation and optimization
   - Channel mix strategy
   - Audience targeting and segmentation
   - Creative and messaging strategy
   - Testing and experimentation (A/B, multivariate)

6. **Data Analysis**
   - Trend identification
   - Anomaly detection
   - Correlation analysis
   - Forecasting
   - Statistical significance

When analyzing data, you should:
- Compare performance against industry benchmarks
- Identify patterns, trends, and anomalies
- Provide specific, actionable recommendations
- Consider the full marketing funnel
- Think about both short-term optimizations and long-term strategy
- Acknowledge data limitations and uncertainty
- Suggest follow-up analyses when appropriate

Be specific with numbers and percentages. Don't just say "good" or "bad" - quantify the performance relative to benchmarks and goals.
"""


class MarketingIntelligence:
    """Advanced marketing analytics and intelligence service."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model

    def analyze_performance(self, data: list[dict], schema_info: dict, question: str,
                            advertiser_context: Optional[dict] = None) -> dict:
        """
        Perform deep marketing analysis on the data.

        Returns comprehensive insights including:
        - Performance assessment vs benchmarks
        - Trend analysis
        - Anomaly detection
        - Strategic recommendations
        - Follow-up questions
        """
        # Prepare data summary
        data_summary = self._prepare_data_summary(data, schema_info)

        # Format advertiser context
        context_section = self._format_advertiser_context(advertiser_context)

        prompt = f"""{MARKETING_SYSTEM_PROMPT}

## ANALYSIS REQUEST
{question}

## DATA SUMMARY
{json.dumps(data_summary, indent=2)}

## FULL DATA (first 100 rows)
{json.dumps(data[:100], indent=2, default=str)}

## INDUSTRY BENCHMARKS FOR REFERENCE
{json.dumps(INDUSTRY_BENCHMARKS, indent=2)}

## ROAS BENCHMARKS BY BUSINESS TYPE
{json.dumps(ROAS_BENCHMARKS, indent=2)}
{context_section}

CRITICAL INSTRUCTIONS:
- If advertiser context is provided above, you MUST follow ALL do's and don'ts exactly
- Compare metrics against the client's specific targets (not just industry benchmarks)
- Apply channel-specific rules when making recommendations
- Consider the client's business model and sales cycle in your analysis

Please provide a comprehensive analysis in the following JSON format:
{{
    "executive_summary": "2-3 sentence high-level summary for executives",

    "performance_assessment": {{
        "overall_health": "healthy|warning|critical",
        "health_score": 0-100,
        "key_metrics": [
            {{
                "metric": "metric name",
                "value": "current value",
                "benchmark": "industry benchmark",
                "assessment": "above_benchmark|at_benchmark|below_benchmark",
                "delta_percentage": "+/- X%"
            }}
        ]
    }},

    "deep_insights": [
        {{
            "category": "trend|anomaly|opportunity|risk|correlation",
            "title": "Short title",
            "insight": "Detailed explanation with specific numbers",
            "confidence": "high|medium|low",
            "impact": "high|medium|low"
        }}
    ],

    "funnel_analysis": {{
        "awareness": {{"metrics": {{}}, "assessment": ""}},
        "consideration": {{"metrics": {{}}, "assessment": ""}},
        "conversion": {{"metrics": {{}}, "assessment": ""}},
        "bottleneck": "Stage with biggest drop-off",
        "recommendation": "How to address the bottleneck"
    }},

    "channel_analysis": [
        {{
            "channel": "channel name",
            "role": "awareness|consideration|conversion|retention",
            "efficiency_score": 0-100,
            "strengths": ["list"],
            "weaknesses": ["list"],
            "recommendation": "specific action"
        }}
    ],

    "budget_recommendations": {{
        "current_allocation": {{"channel": "percentage"}},
        "recommended_allocation": {{"channel": "percentage"}},
        "rationale": "Why these changes",
        "expected_impact": "Projected improvement"
    }},

    "anomalies_detected": [
        {{
            "type": "spike|drop|unusual_pattern",
            "metric": "affected metric",
            "when": "time period",
            "magnitude": "how significant",
            "possible_causes": ["list of causes"],
            "recommended_action": "what to do"
        }}
    ],

    "strategic_recommendations": [
        {{
            "priority": "high|medium|low",
            "timeframe": "immediate|short_term|long_term",
            "recommendation": "Specific action to take",
            "expected_outcome": "What improvement to expect",
            "effort": "low|medium|high",
            "impact": "low|medium|high"
        }}
    ],

    "testing_suggestions": [
        {{
            "test_type": "A/B test|multivariate|incrementality",
            "hypothesis": "What we're testing",
            "variables": ["what to change"],
            "success_metric": "How to measure",
            "estimated_duration": "How long to run"
        }}
    ],

    "follow_up_questions": [
        "Questions to dig deeper into the data"
    ],

    "data_quality_notes": [
        "Any concerns about data quality or completeness"
    ]
}}"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text

        try:
            # Extract JSON from response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response_text[json_start:json_end])
        except json.JSONDecodeError:
            pass

        # Fallback response
        return {
            "executive_summary": response_text[:500],
            "deep_insights": [{"insight": response_text}],
            "strategic_recommendations": [],
            "follow_up_questions": []
        }

    def _prepare_data_summary(self, data: list[dict], schema_info: dict) -> dict:
        """Prepare a statistical summary of the data for analysis."""
        if not data:
            return {"error": "No data available"}

        import pandas as pd
        import numpy as np

        df = pd.DataFrame(data)

        summary = {
            "total_rows": len(df),
            "date_range": {},
            "totals": {},
            "averages": {},
            "by_dimension": {}
        }

        # Date range
        date_cols = [col for col in df.columns if 'date' in col.lower()]
        for col in date_cols:
            try:
                dates = pd.to_datetime(df[col])
                summary["date_range"] = {
                    "start": str(dates.min()),
                    "end": str(dates.max()),
                    "days": (dates.max() - dates.min()).days
                }
                break
            except:
                pass

        # Numeric summaries
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col in ['spend', 'cost', 'revenue', 'impressions', 'clicks', 'conversions']:
                summary["totals"][col] = float(df[col].sum())
            if col in ['ctr', 'cpc', 'cpm', 'cpa', 'roas', 'conversion_rate']:
                summary["averages"][col] = float(df[col].mean())

        # Breakdowns by dimension
        dimension_cols = ['channel', 'campaign', 'source', 'medium']
        for dim in dimension_cols:
            if dim in df.columns:
                breakdown = df.groupby(dim).agg({
                    col: 'sum' for col in numeric_cols if col in ['spend', 'revenue', 'clicks', 'conversions', 'impressions']
                }).to_dict('index')
                summary["by_dimension"][dim] = breakdown

        # Calculate overall metrics
        if summary["totals"].get("spend") and summary["totals"].get("revenue"):
            summary["totals"]["overall_roas"] = round(
                summary["totals"]["revenue"] / summary["totals"]["spend"], 2
            )

        if summary["totals"].get("spend") and summary["totals"].get("conversions"):
            summary["totals"]["overall_cpa"] = round(
                summary["totals"]["spend"] / max(summary["totals"]["conversions"], 1), 2
            )

        if summary["totals"].get("clicks") and summary["totals"].get("impressions"):
            summary["totals"]["overall_ctr"] = round(
                summary["totals"]["clicks"] / summary["totals"]["impressions"] * 100, 2
            )

        return summary

    def compare_to_benchmarks(self, metrics: dict, channel: str = None) -> dict:
        """Compare metrics against industry benchmarks."""
        results = {}

        benchmarks = INDUSTRY_BENCHMARKS.get(channel, {}) if channel else {}

        for metric, value in metrics.items():
            if metric in benchmarks:
                bench = benchmarks[metric]
                results[metric] = {
                    "value": value,
                    "benchmark_low": bench["low"],
                    "benchmark_avg": bench["avg"],
                    "benchmark_high": bench["high"],
                    "unit": bench["unit"],
                    "assessment": self._assess_metric(value, bench)
                }

        return results

    def _assess_metric(self, value: float, benchmark: dict) -> str:
        """Assess a metric value against its benchmark."""
        if value >= benchmark["high"]:
            return "excellent"
        elif value >= benchmark["avg"]:
            return "good"
        elif value >= benchmark["low"]:
            return "fair"
        else:
            return "needs_improvement"

    def generate_narrative_report(self, analysis: dict) -> str:
        """Generate a human-readable narrative report from analysis."""
        prompt = f"""Based on this marketing analysis data, write a clear, executive-friendly narrative report.

ANALYSIS DATA:
{json.dumps(analysis, indent=2)}

Write a 3-5 paragraph report that:
1. Opens with the key headline/takeaway
2. Highlights the most important findings with specific numbers
3. Explains any concerning trends or opportunities
4. Closes with prioritized action items

Use clear business language, not technical jargon. Be specific with numbers and percentages."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    def _format_advertiser_context(self, context: Optional[dict]) -> str:
        """Format advertiser context for inclusion in prompts."""
        if not context:
            return ""

        lines = ["\n\n## ADVERTISER CONTEXT (MUST FOLLOW)"]

        if context.get("name"):
            lines.append(f"**Client:** {context['name']}")

        if context.get("industry"):
            lines.append(f"**Industry:** {context['industry']}")

        if context.get("business_model"):
            lines.append(f"**Business Model:** {context['business_model']}")

        if context.get("sales_cycle_days"):
            lines.append(f"**Sales Cycle:** {context['sales_cycle_days']} days")

        if context.get("primary_kpi"):
            lines.append(f"**Primary KPI:** {context['primary_kpi']}")

        if context.get("secondary_kpis"):
            lines.append(f"**Secondary KPIs:** {', '.join(context['secondary_kpis'])}")

        # Client-specific targets (override benchmarks)
        targets = []
        if context.get("target_cpa"):
            targets.append(f"CPA Target: <${context['target_cpa']}")
        if context.get("target_roas"):
            targets.append(f"ROAS Target: >{context['target_roas']}x")
        if context.get("target_ctr"):
            targets.append(f"CTR Target: >{context['target_ctr']}%")
        if targets:
            lines.append(f"**Client Targets:** {', '.join(targets)}")
            lines.append("(Use these targets instead of generic industry benchmarks)")

        # Client-provided benchmarks
        if context.get("industry_benchmarks"):
            benchmarks = context["industry_benchmarks"]
            bench_str = ", ".join([f"{k}: {v}" for k, v in benchmarks.items()])
            lines.append(f"**Client Industry Benchmarks:** {bench_str}")

        # Channel-specific rules
        if context.get("channel_rules"):
            lines.append("\n**Channel-Specific Rules (MUST FOLLOW):**")
            for rule in context["channel_rules"]:
                lines.append(f"  - **{rule.get('channel', 'Unknown')}**: {rule.get('rule', '')}")

        # Attribution preferences
        if context.get("attribution_window_days"):
            lines.append(f"\n**Attribution Window:** {context['attribution_window_days']} days")
        if context.get("preferred_attribution_model"):
            lines.append(f"**Preferred Attribution:** {context['preferred_attribution_model']}")

        # Do's - CRITICAL
        if context.get("dos"):
            lines.append("\n**DO (Required behaviors):**")
            for do in context["dos"]:
                lines.append(f"  - {do}")

        # Don'ts - CRITICAL
        if context.get("donts"):
            lines.append("\n**DO NOT (Forbidden recommendations):**")
            for dont in context["donts"]:
                lines.append(f"  - {dont}")

        # Custom instructions
        if context.get("custom_instructions"):
            lines.append(f"\n**Additional Client Instructions:**\n{context['custom_instructions']}")

        return "\n".join(lines)
