"""
Conversion Rate Analytics Service

Deep conversion analysis including:
- Multi-stage funnel analysis
- Conversion rate by segment
- Statistical significance testing
- Conversion rate trends and patterns
- Drop-off analysis
- Conversion optimization recommendations
"""

import pandas as pd
import numpy as np
from typing import Optional
from scipy import stats


class ConversionAnalytics:
    """Deep conversion rate analysis."""

    def analyze_conversion_funnel(self, df: pd.DataFrame) -> dict:
        """
        Analyze the full conversion funnel.

        Funnel stages: Impressions → Clicks → Conversions → Revenue
        """
        funnel_metrics = {}

        # Define funnel stages in order
        stages = [
            ("impressions", "Impressions"),
            ("clicks", "Clicks"),
            ("conversions", "Conversions"),
        ]

        available_stages = [(col, name) for col, name in stages if col in df.columns]

        if len(available_stages) < 2:
            return {"error": "Insufficient funnel data. Need at least impressions and clicks."}

        # Calculate totals for each stage
        stage_totals = []
        for col, name in available_stages:
            total = df[col].sum()
            stage_totals.append({
                "stage": name,
                "column": col,
                "total": float(total)
            })

        # Calculate stage-to-stage conversion rates
        funnel_metrics["stages"] = stage_totals
        funnel_metrics["stage_conversions"] = []

        for i in range(1, len(stage_totals)):
            prev = stage_totals[i - 1]
            curr = stage_totals[i]

            if prev["total"] > 0:
                rate = (curr["total"] / prev["total"]) * 100
                drop_off = 100 - rate
            else:
                rate = 0
                drop_off = 100

            funnel_metrics["stage_conversions"].append({
                "from_stage": prev["stage"],
                "to_stage": curr["stage"],
                "conversion_rate": round(rate, 2),
                "drop_off_rate": round(drop_off, 2),
                "volume_lost": float(prev["total"] - curr["total"])
            })

        # Identify biggest bottleneck
        if funnel_metrics["stage_conversions"]:
            bottleneck = max(funnel_metrics["stage_conversions"],
                           key=lambda x: x["drop_off_rate"])
            funnel_metrics["biggest_bottleneck"] = {
                "stage": f"{bottleneck['from_stage']} → {bottleneck['to_stage']}",
                "drop_off_rate": bottleneck["drop_off_rate"],
                "recommendation": self._get_bottleneck_recommendation(
                    bottleneck["from_stage"], bottleneck["to_stage"], bottleneck["drop_off_rate"]
                )
            }

        # Overall funnel efficiency
        if stage_totals[0]["total"] > 0 and len(stage_totals) > 1:
            overall_rate = (stage_totals[-1]["total"] / stage_totals[0]["total"]) * 100
            funnel_metrics["overall_conversion_rate"] = round(overall_rate, 4)

        return funnel_metrics

    def _get_bottleneck_recommendation(self, from_stage: str, to_stage: str, drop_off: float) -> str:
        """Generate recommendation based on bottleneck location."""
        if from_stage == "Impressions" and to_stage == "Clicks":
            if drop_off > 99:
                return "CTR is very low. Test new ad creatives, improve targeting, or adjust bidding strategy."
            elif drop_off > 97:
                return "CTR below average. A/B test headlines, images, and CTAs. Consider audience refinement."
            else:
                return "CTR is reasonable. Focus on scaling while maintaining quality."

        elif from_stage == "Clicks" and to_stage == "Conversions":
            if drop_off > 95:
                return "Very high click-to-conversion drop-off. Audit landing pages, check page load speed, ensure message match."
            elif drop_off > 90:
                return "Conversion rate needs improvement. Test landing page variations, simplify forms, add trust signals."
            else:
                return "Conversion rate is healthy. Consider scaling traffic or testing upsells."

        return f"High drop-off at {from_stage} → {to_stage}. Investigate user experience at this stage."

    def conversion_rate_by_segment(self, df: pd.DataFrame, segment_col: str) -> dict:
        """
        Analyze conversion rates by segment with statistical comparison.
        """
        if segment_col not in df.columns:
            return {"error": f"Column {segment_col} not found"}

        if 'clicks' not in df.columns or 'conversions' not in df.columns:
            return {"error": "Need clicks and conversions columns"}

        # Aggregate by segment
        segment_data = df.groupby(segment_col).agg({
            'impressions': 'sum' if 'impressions' in df.columns else lambda x: 0,
            'clicks': 'sum',
            'conversions': 'sum',
            'spend': 'sum' if 'spend' in df.columns else lambda x: 0,
            'revenue': 'sum' if 'revenue' in df.columns else lambda x: 0,
        }).reset_index()

        segments = []
        for _, row in segment_data.iterrows():
            segment = {
                "segment": row[segment_col],
                "clicks": int(row['clicks']),
                "conversions": int(row['conversions']),
                "conversion_rate": round((row['conversions'] / row['clicks'] * 100), 2) if row['clicks'] > 0 else 0,
            }

            if 'impressions' in df.columns:
                segment["impressions"] = int(row['impressions'])
                segment["ctr"] = round((row['clicks'] / row['impressions'] * 100), 2) if row['impressions'] > 0 else 0

            if 'spend' in df.columns:
                segment["spend"] = float(row['spend'])
                segment["cpa"] = round(row['spend'] / row['conversions'], 2) if row['conversions'] > 0 else None

            if 'revenue' in df.columns:
                segment["revenue"] = float(row['revenue'])
                segment["roas"] = round(row['revenue'] / row['spend'], 2) if row['spend'] > 0 else None

            segments.append(segment)

        # Sort by conversion rate
        segments.sort(key=lambda x: x["conversion_rate"], reverse=True)

        # Statistical comparison (chi-square test)
        if len(segments) >= 2:
            stat_comparison = self._compare_conversion_rates(segments)
        else:
            stat_comparison = None

        # Calculate averages
        total_clicks = sum(s["clicks"] for s in segments)
        total_conversions = sum(s["conversions"] for s in segments)
        avg_conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0

        return {
            "segment_by": segment_col,
            "segments": segments,
            "best_performer": segments[0]["segment"] if segments else None,
            "worst_performer": segments[-1]["segment"] if segments else None,
            "average_conversion_rate": round(avg_conversion_rate, 2),
            "statistical_comparison": stat_comparison,
            "recommendations": self._generate_segment_recommendations(segments, avg_conversion_rate)
        }

    def _compare_conversion_rates(self, segments: list) -> dict:
        """
        Compare conversion rates using chi-square test.
        Determines if differences are statistically significant.
        """
        # Build contingency table
        conversions = [s["conversions"] for s in segments]
        non_conversions = [s["clicks"] - s["conversions"] for s in segments]

        # Chi-square test
        contingency_table = [conversions, non_conversions]

        try:
            chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)

            return {
                "test": "chi_square",
                "chi2_statistic": round(chi2, 4),
                "p_value": round(p_value, 6),
                "degrees_of_freedom": dof,
                "significant_at_95": p_value < 0.05,
                "significant_at_99": p_value < 0.01,
                "interpretation": self._interpret_significance(p_value)
            }
        except Exception as e:
            return {"error": str(e)}

    def _interpret_significance(self, p_value: float) -> str:
        """Interpret statistical significance."""
        if p_value < 0.01:
            return "Highly significant difference. The conversion rate variations are very unlikely due to chance."
        elif p_value < 0.05:
            return "Significant difference. You can be confident these variations are real, not random."
        elif p_value < 0.1:
            return "Marginally significant. There may be a real difference, but more data would help confirm."
        else:
            return "Not statistically significant. Observed differences could be due to random variation."

    def _generate_segment_recommendations(self, segments: list, avg_rate: float) -> list:
        """Generate recommendations based on segment performance."""
        recommendations = []

        for segment in segments:
            rate = segment["conversion_rate"]
            name = segment["segment"]

            if rate > avg_rate * 1.5:
                recommendations.append({
                    "segment": name,
                    "action": "scale",
                    "recommendation": f"{name} converts {round(rate/avg_rate, 1)}x better than average. Increase budget allocation."
                })
            elif rate < avg_rate * 0.5:
                recommendations.append({
                    "segment": name,
                    "action": "optimize_or_pause",
                    "recommendation": f"{name} converts at {round(rate/avg_rate*100)}% of average. Consider pausing or testing new approach."
                })

        return recommendations

    def conversion_trend_analysis(self, df: pd.DataFrame, date_col: str = 'date') -> dict:
        """Analyze conversion rate trends over time."""
        if date_col not in df.columns:
            return {"error": f"Date column {date_col} not found"}

        if 'clicks' not in df.columns or 'conversions' not in df.columns:
            return {"error": "Need clicks and conversions columns"}

        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])

        # Aggregate by date
        daily = df.groupby(date_col).agg({
            'clicks': 'sum',
            'conversions': 'sum',
            'spend': 'sum' if 'spend' in df.columns else lambda x: 0,
        }).reset_index()

        daily['conversion_rate'] = np.where(
            daily['clicks'] > 0,
            (daily['conversions'] / daily['clicks'] * 100).round(2),
            0
        )

        # Calculate trend
        if len(daily) >= 3:
            x = np.arange(len(daily))
            y = daily['conversion_rate'].values
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

            trend = {
                "direction": "improving" if slope > 0 else "declining" if slope < 0 else "stable",
                "slope_per_day": round(slope, 4),
                "r_squared": round(r_value ** 2, 4),
                "statistically_significant": p_value < 0.05,
                "p_value": round(p_value, 4)
            }
        else:
            trend = {"direction": "insufficient_data"}

        # Week-over-week comparison
        if len(daily) >= 14:
            recent_week = daily.tail(7)
            previous_week = daily.iloc[-14:-7]

            recent_rate = (recent_week['conversions'].sum() / recent_week['clicks'].sum() * 100) if recent_week['clicks'].sum() > 0 else 0
            previous_rate = (previous_week['conversions'].sum() / previous_week['clicks'].sum() * 100) if previous_week['clicks'].sum() > 0 else 0

            wow_change = ((recent_rate - previous_rate) / previous_rate * 100) if previous_rate > 0 else 0

            week_comparison = {
                "recent_week_rate": round(recent_rate, 2),
                "previous_week_rate": round(previous_rate, 2),
                "change_percentage": round(wow_change, 2),
                "direction": "up" if wow_change > 0 else "down" if wow_change < 0 else "flat"
            }
        else:
            week_comparison = None

        return {
            "daily_data": daily.to_dict('records'),
            "trend": trend,
            "week_over_week": week_comparison,
            "overall_rate": round(
                (daily['conversions'].sum() / daily['clicks'].sum() * 100), 2
            ) if daily['clicks'].sum() > 0 else 0,
            "best_day": daily.loc[daily['conversion_rate'].idxmax()].to_dict() if len(daily) > 0 else None,
            "worst_day": daily.loc[daily['conversion_rate'].idxmin()].to_dict() if len(daily) > 0 else None,
        }

    def ab_test_analysis(self, variant_a: dict, variant_b: dict) -> dict:
        """
        Analyze A/B test results for conversion rate.

        Args:
            variant_a: {"name": str, "visitors": int, "conversions": int}
            variant_b: {"name": str, "visitors": int, "conversions": int}
        """
        n_a = variant_a["visitors"]
        c_a = variant_a["conversions"]
        n_b = variant_b["visitors"]
        c_b = variant_b["conversions"]

        rate_a = c_a / n_a if n_a > 0 else 0
        rate_b = c_b / n_b if n_b > 0 else 0

        # Relative lift
        lift = ((rate_b - rate_a) / rate_a * 100) if rate_a > 0 else 0

        # Chi-square test
        contingency = [[c_a, n_a - c_a], [c_b, n_b - c_b]]
        try:
            chi2, p_value, _, _ = stats.chi2_contingency(contingency)

            # Calculate confidence interval using normal approximation
            se = np.sqrt(rate_a * (1 - rate_a) / n_a + rate_b * (1 - rate_b) / n_b)
            ci_95 = (round((rate_b - rate_a - 1.96 * se) * 100, 2),
                    round((rate_b - rate_a + 1.96 * se) * 100, 2))

            result = {
                "variant_a": {
                    "name": variant_a["name"],
                    "visitors": n_a,
                    "conversions": c_a,
                    "conversion_rate": round(rate_a * 100, 2)
                },
                "variant_b": {
                    "name": variant_b["name"],
                    "visitors": n_b,
                    "conversions": c_b,
                    "conversion_rate": round(rate_b * 100, 2)
                },
                "relative_lift": round(lift, 2),
                "absolute_difference": round((rate_b - rate_a) * 100, 2),
                "confidence_interval_95": ci_95,
                "p_value": round(p_value, 6),
                "statistically_significant": p_value < 0.05,
                "winner": variant_b["name"] if rate_b > rate_a and p_value < 0.05 else
                         variant_a["name"] if rate_a > rate_b and p_value < 0.05 else "no_winner_yet",
                "recommendation": self._ab_test_recommendation(rate_a, rate_b, p_value, n_a + n_b)
            }
        except Exception as e:
            result = {"error": str(e)}

        return result

    def _ab_test_recommendation(self, rate_a: float, rate_b: float, p_value: float, total_n: int) -> str:
        """Generate A/B test recommendation."""
        if p_value < 0.05:
            winner = "B" if rate_b > rate_a else "A"
            lift = abs((rate_b - rate_a) / rate_a * 100) if rate_a > 0 else 0
            return f"Variant {winner} wins with {lift:.1f}% lift. Implement the winning variant."
        elif p_value < 0.1:
            return f"Results are marginally significant. Consider running longer to reach 95% confidence."
        elif total_n < 1000:
            return f"Need more data. Current sample size ({total_n}) may be too small for detection."
        else:
            return "No significant difference detected. The variants perform similarly."

    def sample_size_calculator(self, baseline_rate: float, minimum_detectable_effect: float,
                               confidence: float = 0.95, power: float = 0.8) -> dict:
        """
        Calculate required sample size for A/B test.

        Args:
            baseline_rate: Current conversion rate (e.g., 0.05 for 5%)
            minimum_detectable_effect: Relative change to detect (e.g., 0.1 for 10% lift)
            confidence: Confidence level (default 0.95)
            power: Statistical power (default 0.8)
        """
        from scipy.stats import norm

        alpha = 1 - confidence
        z_alpha = norm.ppf(1 - alpha / 2)
        z_beta = norm.ppf(power)

        p1 = baseline_rate
        p2 = baseline_rate * (1 + minimum_detectable_effect)

        # Pooled proportion
        p_pooled = (p1 + p2) / 2

        # Sample size per variant
        n = (2 * p_pooled * (1 - p_pooled) * (z_alpha + z_beta) ** 2) / ((p2 - p1) ** 2)
        n = int(np.ceil(n))

        # Estimate test duration
        # Assuming you need this many conversions to detect effect

        return {
            "sample_size_per_variant": n,
            "total_sample_size": n * 2,
            "baseline_rate": round(baseline_rate * 100, 2),
            "target_rate": round(p2 * 100, 2),
            "minimum_detectable_effect": f"{minimum_detectable_effect * 100}%",
            "confidence_level": f"{confidence * 100}%",
            "statistical_power": f"{power * 100}%",
            "interpretation": f"You need {n:,} visitors per variant ({n*2:,} total) to detect a {minimum_detectable_effect*100}% change in conversion rate with {confidence*100}% confidence."
        }
