"""
Incrementality Analysis Service

Measure true causal impact of marketing spend:
- Time-based incrementality (before/after analysis)
- Channel incrementality estimation
- Geo-lift analysis framework
- Holdout test design
- Causal inference methods
- Diminishing returns analysis
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple
from scipy import stats
from datetime import datetime, timedelta


class IncrementalityAnalyzer:
    """
    Measure true incremental impact of marketing activities.

    Incrementality answers: "What would have happened WITHOUT this marketing spend?"
    vs Attribution which answers: "Who gets credit for this conversion?"
    """

    def estimate_channel_incrementality(self, df: pd.DataFrame) -> dict:
        """
        Estimate incrementality by channel using statistical methods.

        This uses correlation and regression analysis to estimate what portion
        of conversions are truly incremental vs would have happened anyway.
        """
        if 'channel' not in df.columns:
            return {"error": "Channel column required"}

        required = ['spend', 'conversions']
        if not all(col in df.columns for col in required):
            return {"error": f"Required columns: {required}"}

        results = {
            "methodology": "regression_based_estimation",
            "disclaimer": "True incrementality requires controlled experiments (holdout tests). These are statistical estimates.",
            "channels": []
        }

        # Analyze each channel
        for channel in df['channel'].unique():
            channel_data = df[df['channel'] == channel].copy()

            if len(channel_data) < 7:
                continue

            # Calculate efficiency metrics
            total_spend = channel_data['spend'].sum()
            total_conversions = channel_data['conversions'].sum()

            if total_spend == 0:
                continue

            # Estimate incrementality using spend-conversion correlation
            # Higher correlation suggests more incremental impact
            if len(channel_data) >= 5:
                correlation, p_value = stats.pearsonr(
                    channel_data['spend'],
                    channel_data['conversions']
                )

                # Calculate marginal efficiency (conversions per $ at different spend levels)
                marginal_analysis = self._analyze_marginal_returns(channel_data)

                # Estimate incrementality rate
                # This is a simplified model - true incrementality needs experiments
                incrementality_estimate = self._estimate_incrementality_rate(
                    correlation, p_value, marginal_analysis
                )
            else:
                correlation = None
                p_value = None
                incrementality_estimate = None
                marginal_analysis = None

            results["channels"].append({
                "channel": channel,
                "total_spend": round(total_spend, 2),
                "total_conversions": int(total_conversions),
                "attributed_cpa": round(total_spend / total_conversions, 2) if total_conversions > 0 else None,
                "spend_conversion_correlation": round(correlation, 3) if correlation else None,
                "correlation_p_value": round(p_value, 4) if p_value else None,
                "estimated_incrementality_rate": incrementality_estimate,
                "estimated_incremental_conversions": int(total_conversions * incrementality_estimate) if incrementality_estimate else None,
                "estimated_incremental_cpa": round(total_spend / (total_conversions * incrementality_estimate), 2) if incrementality_estimate and total_conversions > 0 else None,
                "marginal_returns": marginal_analysis,
                "confidence": "low" if not p_value or p_value > 0.1 else "medium" if p_value > 0.05 else "high"
            })

        # Sort by estimated incrementality
        results["channels"].sort(
            key=lambda x: x.get("estimated_incrementality_rate") or 0,
            reverse=True
        )

        # Generate recommendations
        results["recommendations"] = self._generate_incrementality_recommendations(results["channels"])

        return results

    def _analyze_marginal_returns(self, df: pd.DataFrame) -> dict:
        """Analyze marginal returns (diminishing returns)."""
        if len(df) < 5:
            return None

        df = df.sort_values('spend')

        # Split into quartiles by spend
        df['spend_quartile'] = pd.qcut(df['spend'], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'])

        quartile_efficiency = {}
        for q in ['Q1', 'Q2', 'Q3', 'Q4']:
            q_data = df[df['spend_quartile'] == q]
            if len(q_data) > 0 and q_data['spend'].sum() > 0:
                efficiency = q_data['conversions'].sum() / q_data['spend'].sum()
                quartile_efficiency[q] = round(efficiency, 4)

        # Check for diminishing returns
        efficiencies = list(quartile_efficiency.values())
        if len(efficiencies) >= 2:
            if efficiencies[-1] < efficiencies[0] * 0.7:
                pattern = "strong_diminishing_returns"
            elif efficiencies[-1] < efficiencies[0] * 0.9:
                pattern = "moderate_diminishing_returns"
            elif efficiencies[-1] > efficiencies[0] * 1.1:
                pattern = "increasing_returns"
            else:
                pattern = "constant_returns"
        else:
            pattern = "insufficient_data"

        return {
            "efficiency_by_spend_level": quartile_efficiency,
            "pattern": pattern,
            "interpretation": self._interpret_marginal_returns(pattern)
        }

    def _interpret_marginal_returns(self, pattern: str) -> str:
        """Interpret marginal returns pattern."""
        interpretations = {
            "strong_diminishing_returns": "Strong diminishing returns detected. Additional spend yields significantly fewer conversions. Consider reallocating budget.",
            "moderate_diminishing_returns": "Moderate diminishing returns. Efficiency decreases at higher spend levels. May be approaching saturation.",
            "increasing_returns": "Increasing returns detected. Higher spend is more efficient. Channel may be underfunded.",
            "constant_returns": "Relatively constant returns across spend levels. Channel scales linearly.",
            "insufficient_data": "Not enough data to determine return pattern."
        }
        return interpretations.get(pattern, "Unknown pattern")

    def _estimate_incrementality_rate(self, correlation: float, p_value: float,
                                      marginal_analysis: dict) -> Optional[float]:
        """
        Estimate what % of conversions are truly incremental.

        This is a heuristic model based on:
        1. Spend-conversion correlation (higher = more incremental)
        2. Marginal returns pattern (diminishing returns = hitting organic baseline)
        3. Statistical significance

        True incrementality requires experiments, but this gives directional guidance.
        """
        if correlation is None or p_value is None:
            return None

        # Base incrementality on correlation strength
        # Perfect correlation (1.0) suggests fully incremental
        # No correlation (0.0) suggests all organic
        base_rate = max(0, min(1, (correlation + 1) / 2))  # Normalize to 0-1

        # Adjust for statistical significance
        if p_value > 0.1:
            confidence_multiplier = 0.5  # Low confidence
        elif p_value > 0.05:
            confidence_multiplier = 0.7  # Medium confidence
        else:
            confidence_multiplier = 1.0  # High confidence

        # Adjust for marginal returns
        if marginal_analysis:
            pattern = marginal_analysis.get("pattern", "")
            if pattern == "strong_diminishing_returns":
                returns_multiplier = 0.6  # Some conversions are baseline
            elif pattern == "moderate_diminishing_returns":
                returns_multiplier = 0.8
            elif pattern == "increasing_returns":
                returns_multiplier = 1.0  # Likely all incremental
            else:
                returns_multiplier = 0.85  # Default assumption
        else:
            returns_multiplier = 0.85

        incrementality_rate = base_rate * confidence_multiplier * returns_multiplier

        # Cap at reasonable bounds
        incrementality_rate = max(0.3, min(0.95, incrementality_rate))

        return round(incrementality_rate, 2)

    def _generate_incrementality_recommendations(self, channels: list) -> list:
        """Generate recommendations based on incrementality analysis."""
        recommendations = []

        for ch in channels:
            inc_rate = ch.get("estimated_incrementality_rate")
            channel = ch.get("channel")

            if inc_rate is None:
                continue

            if inc_rate < 0.5:
                recommendations.append({
                    "channel": channel,
                    "priority": "high",
                    "action": "test_incrementality",
                    "recommendation": f"{channel} shows low estimated incrementality ({inc_rate*100:.0f}%). Run a holdout test to validate before continuing spend."
                })
            elif inc_rate > 0.8:
                recommendations.append({
                    "channel": channel,
                    "priority": "medium",
                    "action": "scale_carefully",
                    "recommendation": f"{channel} appears highly incremental ({inc_rate*100:.0f}%). Consider increasing budget while monitoring for diminishing returns."
                })

        # Check for reallocation opportunities
        if len(channels) >= 2:
            sorted_channels = sorted(channels, key=lambda x: x.get("estimated_incrementality_rate") or 0, reverse=True)
            best = sorted_channels[0]
            worst = sorted_channels[-1]

            if best.get("estimated_incrementality_rate", 0) > worst.get("estimated_incrementality_rate", 1) + 0.2:
                recommendations.append({
                    "priority": "high",
                    "action": "reallocate",
                    "recommendation": f"Consider shifting budget from {worst['channel']} ({worst.get('estimated_incrementality_rate', 0)*100:.0f}% incremental) to {best['channel']} ({best.get('estimated_incrementality_rate', 0)*100:.0f}% incremental)."
                })

        return recommendations

    def time_based_incrementality(self, df: pd.DataFrame, date_col: str = 'date',
                                  treatment_start: str = None) -> dict:
        """
        Estimate incrementality using time-based analysis (before/after).

        If treatment_start is provided, compares performance before/after.
        Otherwise, identifies significant changes automatically.
        """
        if date_col not in df.columns:
            return {"error": f"Date column {date_col} not found"}

        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col)

        required = ['conversions']
        if not all(col in df.columns for col in required):
            return {"error": f"Required columns: {required}"}

        # Aggregate by date
        daily = df.groupby(date_col).agg({
            'conversions': 'sum',
            'spend': 'sum' if 'spend' in df.columns else lambda x: 0,
            'revenue': 'sum' if 'revenue' in df.columns else lambda x: 0,
        }).reset_index()

        if treatment_start:
            treatment_date = pd.to_datetime(treatment_start)
        else:
            # Find midpoint for analysis
            treatment_date = daily[date_col].iloc[len(daily) // 2]

        pre_period = daily[daily[date_col] < treatment_date]
        post_period = daily[daily[date_col] >= treatment_date]

        if len(pre_period) < 3 or len(post_period) < 3:
            return {"error": "Insufficient data in pre or post period"}

        # Calculate metrics for each period
        pre_metrics = {
            "avg_daily_conversions": pre_period['conversions'].mean(),
            "total_conversions": pre_period['conversions'].sum(),
            "days": len(pre_period)
        }
        post_metrics = {
            "avg_daily_conversions": post_period['conversions'].mean(),
            "total_conversions": post_period['conversions'].sum(),
            "days": len(post_period)
        }

        # T-test to compare periods
        t_stat, p_value = stats.ttest_ind(
            pre_period['conversions'],
            post_period['conversions']
        )

        # Calculate lift
        if pre_metrics["avg_daily_conversions"] > 0:
            lift = ((post_metrics["avg_daily_conversions"] - pre_metrics["avg_daily_conversions"])
                   / pre_metrics["avg_daily_conversions"] * 100)
        else:
            lift = 0

        # Estimate incremental conversions
        expected_without_change = pre_metrics["avg_daily_conversions"] * post_metrics["days"]
        incremental_conversions = post_metrics["total_conversions"] - expected_without_change

        return {
            "methodology": "time_based_before_after",
            "treatment_date": str(treatment_date)[:10],
            "pre_period": pre_metrics,
            "post_period": post_metrics,
            "lift_percentage": round(lift, 2),
            "incremental_conversions": round(incremental_conversions, 0),
            "t_statistic": round(t_stat, 3),
            "p_value": round(p_value, 4),
            "statistically_significant": p_value < 0.05,
            "interpretation": self._interpret_time_based_result(lift, p_value, incremental_conversions),
            "caveats": [
                "Time-based analysis cannot account for external factors (seasonality, competition, etc.)",
                "True incrementality requires randomized controlled experiments",
                "Results should be validated with holdout tests"
            ]
        }

    def _interpret_time_based_result(self, lift: float, p_value: float, incremental: float) -> str:
        """Interpret time-based incrementality result."""
        if p_value > 0.05:
            return "No statistically significant change detected between periods. Observed differences may be due to random variation."

        if lift > 0:
            return f"Significant positive lift of {lift:.1f}% detected, representing approximately {incremental:.0f} incremental conversions. However, this may be influenced by external factors."
        else:
            return f"Significant negative change of {lift:.1f}% detected. Performance declined in the post period."

    def design_holdout_test(self, current_daily_conversions: float,
                           minimum_detectable_lift: float = 0.1,
                           confidence: float = 0.95,
                           power: float = 0.8) -> dict:
        """
        Design a holdout test to measure true incrementality.

        Args:
            current_daily_conversions: Current average daily conversions
            minimum_detectable_lift: Minimum lift to detect (e.g., 0.1 = 10%)
            confidence: Statistical confidence level
            power: Statistical power
        """
        from scipy.stats import norm

        alpha = 1 - confidence
        z_alpha = norm.ppf(1 - alpha / 2)
        z_beta = norm.ppf(power)

        # For count data, use Poisson approximation
        # Variance ≈ mean for Poisson
        variance = current_daily_conversions
        effect_size = current_daily_conversions * minimum_detectable_lift

        # Sample size per group per day
        n_per_day = (2 * variance * (z_alpha + z_beta) ** 2) / (effect_size ** 2)

        # Estimate test duration
        # Need enough conversions to detect effect
        min_conversions_needed = int(np.ceil(n_per_day))
        test_duration_days = max(7, int(np.ceil(min_conversions_needed / current_daily_conversions)))

        # Holdout percentage recommendation
        # Larger holdout = faster results but more revenue risk
        if test_duration_days <= 14:
            holdout_pct = 10
        elif test_duration_days <= 30:
            holdout_pct = 15
        else:
            holdout_pct = 20

        return {
            "test_design": "randomized_holdout",
            "objective": f"Detect {minimum_detectable_lift*100:.0f}% lift with {confidence*100:.0f}% confidence",
            "parameters": {
                "holdout_percentage": holdout_pct,
                "test_duration_days": test_duration_days,
                "minimum_conversions_needed": min_conversions_needed * 2,
                "confidence_level": f"{confidence*100:.0f}%",
                "statistical_power": f"{power*100:.0f}%"
            },
            "implementation": {
                "step_1": f"Randomly assign {holdout_pct}% of users/traffic to holdout (no ads)",
                "step_2": f"Run test for {test_duration_days} days minimum",
                "step_3": "Compare conversion rates between exposed and holdout groups",
                "step_4": "Calculate incrementality = (exposed_rate - holdout_rate) / exposed_rate"
            },
            "expected_metrics": {
                "control_group_size": f"{holdout_pct}% of traffic",
                "test_group_size": f"{100-holdout_pct}% of traffic",
                "estimated_lost_conversions": round(current_daily_conversions * test_duration_days * (holdout_pct/100), 0)
            },
            "success_criteria": f"If exposed group converts >{minimum_detectable_lift*100:.0f}% better than holdout with p<0.05, channel is incremental"
        }

    def geo_lift_analysis(self, df: pd.DataFrame, geo_col: str,
                         test_geos: list, control_geos: list) -> dict:
        """
        Analyze geo-based lift test results.

        Args:
            df: DataFrame with geo-level data
            geo_col: Column name for geography
            test_geos: List of geographies in test group
            control_geos: List of geographies in control group
        """
        if geo_col not in df.columns:
            return {"error": f"Geo column {geo_col} not found"}

        test_data = df[df[geo_col].isin(test_geos)]
        control_data = df[df[geo_col].isin(control_geos)]

        if len(test_data) == 0 or len(control_data) == 0:
            return {"error": "No data found for specified test or control geos"}

        # Aggregate metrics
        test_metrics = {
            "geos": test_geos,
            "conversions": test_data['conversions'].sum() if 'conversions' in df.columns else 0,
            "spend": test_data['spend'].sum() if 'spend' in df.columns else 0,
            "revenue": test_data['revenue'].sum() if 'revenue' in df.columns else 0,
        }

        control_metrics = {
            "geos": control_geos,
            "conversions": control_data['conversions'].sum() if 'conversions' in df.columns else 0,
            "spend": control_data['spend'].sum() if 'spend' in df.columns else 0,
            "revenue": control_data['revenue'].sum() if 'revenue' in df.columns else 0,
        }

        # Calculate lift
        if control_metrics["conversions"] > 0:
            lift = ((test_metrics["conversions"] / len(test_geos)) /
                   (control_metrics["conversions"] / len(control_geos)) - 1) * 100
        else:
            lift = 0

        # Incrementality calculation
        expected_test_conversions = (control_metrics["conversions"] / len(control_geos)) * len(test_geos)
        incremental_conversions = test_metrics["conversions"] - expected_test_conversions

        if test_metrics["conversions"] > 0:
            incrementality_rate = incremental_conversions / test_metrics["conversions"]
        else:
            incrementality_rate = 0

        return {
            "methodology": "geo_lift_test",
            "test_group": test_metrics,
            "control_group": control_metrics,
            "results": {
                "lift_percentage": round(lift, 2),
                "incremental_conversions": round(incremental_conversions, 0),
                "incrementality_rate": round(incrementality_rate, 2),
                "interpretation": f"{incrementality_rate*100:.0f}% of conversions in test geos are incremental"
            },
            "cost_effectiveness": {
                "attributed_cpa": round(test_metrics["spend"] / test_metrics["conversions"], 2) if test_metrics["conversions"] > 0 else None,
                "incremental_cpa": round(test_metrics["spend"] / incremental_conversions, 2) if incremental_conversions > 0 else None,
            }
        }
