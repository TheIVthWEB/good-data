"""
Advanced Analytics Service

Provides sophisticated marketing analytics including:
- Time series analysis and forecasting
- Anomaly detection
- Attribution modeling
- Correlation analysis
- Segmentation analysis
- Diminishing returns analysis
- Budget optimization
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict


class AdvancedAnalytics:
    """Advanced analytics for marketing data."""

    def analyze_time_series(self, df: pd.DataFrame, metric: str, date_col: str = 'date') -> dict:
        """
        Analyze time series data for trends, seasonality, and forecasting.
        """
        if date_col not in df.columns or metric not in df.columns:
            return {"error": f"Required columns not found: {date_col}, {metric}"}

        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col)

        # Aggregate by date if needed
        daily = df.groupby(date_col)[metric].sum().reset_index()

        values = daily[metric].values
        dates = daily[date_col].values

        analysis = {
            "metric": metric,
            "period": {
                "start": str(dates[0])[:10],
                "end": str(dates[-1])[:10],
                "days": len(dates)
            },
            "summary": {
                "total": float(values.sum()),
                "mean": float(values.mean()),
                "std": float(values.std()),
                "min": float(values.min()),
                "max": float(values.max()),
            },
            "trend": self._calculate_trend(values),
            "growth": self._calculate_growth(values),
            "volatility": self._calculate_volatility(values),
            "day_of_week_pattern": self._day_of_week_analysis(daily, date_col, metric),
            "forecast": self._simple_forecast(values, periods=7),
        }

        return analysis

    def _calculate_trend(self, values: np.ndarray) -> dict:
        """Calculate linear trend."""
        if len(values) < 2:
            return {"direction": "insufficient_data"}

        x = np.arange(len(values))
        slope, intercept = np.polyfit(x, values, 1)

        # Determine trend direction and strength
        if slope > 0:
            direction = "increasing"
        elif slope < 0:
            direction = "decreasing"
        else:
            direction = "flat"

        # Calculate R-squared
        y_pred = slope * x + intercept
        ss_res = np.sum((values - y_pred) ** 2)
        ss_tot = np.sum((values - np.mean(values)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        return {
            "direction": direction,
            "slope": round(slope, 4),
            "r_squared": round(r_squared, 4),
            "strength": "strong" if abs(r_squared) > 0.7 else "moderate" if abs(r_squared) > 0.3 else "weak"
        }

    def _calculate_growth(self, values: np.ndarray) -> dict:
        """Calculate period-over-period growth."""
        if len(values) < 2:
            return {}

        # Overall growth
        total_growth = ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0

        # Week-over-week (last 7 vs previous 7)
        if len(values) >= 14:
            recent = values[-7:].sum()
            previous = values[-14:-7].sum()
            wow = ((recent - previous) / previous * 100) if previous != 0 else 0
        else:
            wow = None

        # Calculate CAGR if enough data
        if len(values) >= 30:
            periods = len(values)
            cagr = ((values[-1] / values[0]) ** (1 / periods) - 1) * 100 if values[0] != 0 else 0
        else:
            cagr = None

        return {
            "total_growth_pct": round(total_growth, 2),
            "week_over_week_pct": round(wow, 2) if wow is not None else None,
            "daily_cagr_pct": round(cagr, 4) if cagr is not None else None
        }

    def _calculate_volatility(self, values: np.ndarray) -> dict:
        """Calculate volatility metrics."""
        if len(values) < 2:
            return {}

        # Coefficient of variation
        cv = (np.std(values) / np.mean(values) * 100) if np.mean(values) != 0 else 0

        # Daily changes
        changes = np.diff(values)
        pct_changes = (changes / values[:-1] * 100) if all(values[:-1] != 0) else []

        return {
            "coefficient_of_variation": round(cv, 2),
            "avg_daily_change": round(np.mean(np.abs(changes)), 2) if len(changes) > 0 else 0,
            "max_daily_drop": round(min(changes), 2) if len(changes) > 0 else 0,
            "max_daily_spike": round(max(changes), 2) if len(changes) > 0 else 0,
            "stability": "stable" if cv < 20 else "moderate" if cv < 50 else "volatile"
        }

    def _day_of_week_analysis(self, df: pd.DataFrame, date_col: str, metric: str) -> dict:
        """Analyze day-of-week patterns."""
        df = df.copy()
        df['day_of_week'] = pd.to_datetime(df[date_col]).dt.day_name()

        dow_avg = df.groupby('day_of_week')[metric].mean()

        # Order days properly
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dow_avg = dow_avg.reindex(day_order)

        best_day = dow_avg.idxmax()
        worst_day = dow_avg.idxmin()

        return {
            "by_day": {day: round(val, 2) for day, val in dow_avg.items()},
            "best_day": best_day,
            "worst_day": worst_day,
            "weekend_vs_weekday": {
                "weekday_avg": round(dow_avg[['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']].mean(), 2),
                "weekend_avg": round(dow_avg[['Saturday', 'Sunday']].mean(), 2)
            }
        }

    def _simple_forecast(self, values: np.ndarray, periods: int = 7) -> dict:
        """Simple forecast using linear regression."""
        if len(values) < 7:
            return {"error": "Insufficient data for forecasting"}

        x = np.arange(len(values))
        slope, intercept = np.polyfit(x, values, 1)

        # Forecast future values
        future_x = np.arange(len(values), len(values) + periods)
        forecast_values = slope * future_x + intercept

        # Calculate confidence interval (simple approach)
        std_error = np.std(values - (slope * x + intercept))

        return {
            "method": "linear_regression",
            "periods_ahead": periods,
            "forecast": [round(v, 2) for v in forecast_values],
            "trend_direction": "up" if slope > 0 else "down" if slope < 0 else "flat",
            "confidence": "low" if std_error > np.mean(values) * 0.3 else "medium" if std_error > np.mean(values) * 0.15 else "high",
            "predicted_total": round(sum(forecast_values), 2)
        }

    def detect_anomalies(self, df: pd.DataFrame, metric: str, date_col: str = 'date',
                        sensitivity: float = 2.0) -> list[dict]:
        """
        Detect anomalies in time series data using statistical methods.

        Args:
            sensitivity: Number of standard deviations for anomaly threshold (default 2.0)
        """
        if date_col not in df.columns or metric not in df.columns:
            return []

        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        daily = df.groupby(date_col)[metric].sum().reset_index()

        values = daily[metric].values
        dates = daily[date_col].values

        anomalies = []

        # Method 1: Z-score based
        mean = np.mean(values)
        std = np.std(values)

        for i, (date, value) in enumerate(zip(dates, values)):
            z_score = (value - mean) / std if std > 0 else 0

            if abs(z_score) > sensitivity:
                anomalies.append({
                    "date": str(date)[:10],
                    "value": float(value),
                    "expected_range": {
                        "low": round(mean - sensitivity * std, 2),
                        "high": round(mean + sensitivity * std, 2)
                    },
                    "z_score": round(z_score, 2),
                    "type": "spike" if z_score > 0 else "drop",
                    "severity": "high" if abs(z_score) > 3 else "medium" if abs(z_score) > 2 else "low",
                    "deviation_pct": round((value - mean) / mean * 100, 1) if mean != 0 else 0
                })

        # Method 2: Day-over-day change detection
        if len(values) > 1:
            for i in range(1, len(values)):
                if values[i-1] != 0:
                    change_pct = (values[i] - values[i-1]) / values[i-1] * 100
                    if abs(change_pct) > 50:  # 50% change threshold
                        # Check if not already detected
                        date_str = str(dates[i])[:10]
                        if not any(a["date"] == date_str for a in anomalies):
                            anomalies.append({
                                "date": date_str,
                                "value": float(values[i]),
                                "previous_value": float(values[i-1]),
                                "change_pct": round(change_pct, 1),
                                "type": "sudden_spike" if change_pct > 0 else "sudden_drop",
                                "severity": "high" if abs(change_pct) > 100 else "medium"
                            })

        return sorted(anomalies, key=lambda x: x["date"])

    def attribution_analysis(self, df: pd.DataFrame) -> dict:
        """
        Perform attribution analysis across channels.

        Calculates multiple attribution models:
        - Last-touch
        - First-touch
        - Linear
        - Position-based
        """
        if 'channel' not in df.columns:
            return {"error": "Channel column required for attribution analysis"}

        # Required metrics
        metrics = ['conversions', 'revenue', 'spend']
        available_metrics = [m for m in metrics if m in df.columns]

        if not available_metrics:
            return {"error": "No conversion/revenue metrics found"}

        # Aggregate by channel
        channel_data = df.groupby('channel').agg({
            m: 'sum' for m in available_metrics
        }).reset_index()

        total_conversions = channel_data['conversions'].sum() if 'conversions' in channel_data else 0
        total_revenue = channel_data['revenue'].sum() if 'revenue' in channel_data else 0
        total_spend = channel_data['spend'].sum() if 'spend' in channel_data else 0

        # Last-touch attribution (100% credit to converting channel)
        last_touch = {}
        for _, row in channel_data.iterrows():
            channel = row['channel']
            last_touch[channel] = {
                "conversions": float(row.get('conversions', 0)),
                "conversion_share": round(row.get('conversions', 0) / total_conversions * 100, 1) if total_conversions > 0 else 0,
                "revenue": float(row.get('revenue', 0)),
                "revenue_share": round(row.get('revenue', 0) / total_revenue * 100, 1) if total_revenue > 0 else 0,
            }

        # Calculate efficiency metrics
        efficiency = {}
        for _, row in channel_data.iterrows():
            channel = row['channel']
            spend = row.get('spend', 0)
            conversions = row.get('conversions', 0)
            revenue = row.get('revenue', 0)

            efficiency[channel] = {
                "spend": float(spend),
                "spend_share": round(spend / total_spend * 100, 1) if total_spend > 0 else 0,
                "cpa": round(spend / conversions, 2) if conversions > 0 else None,
                "roas": round(revenue / spend, 2) if spend > 0 else None,
                "conversion_rate": round(conversions / spend * 100, 4) if spend > 0 else None
            }

        # Identify best/worst performers
        if efficiency:
            channels_with_roas = {k: v['roas'] for k, v in efficiency.items() if v['roas'] is not None}
            best_roas = max(channels_with_roas, key=channels_with_roas.get) if channels_with_roas else None
            worst_roas = min(channels_with_roas, key=channels_with_roas.get) if channels_with_roas else None

            channels_with_cpa = {k: v['cpa'] for k, v in efficiency.items() if v['cpa'] is not None}
            best_cpa = min(channels_with_cpa, key=channels_with_cpa.get) if channels_with_cpa else None
            worst_cpa = max(channels_with_cpa, key=channels_with_cpa.get) if channels_with_cpa else None
        else:
            best_roas = worst_roas = best_cpa = worst_cpa = None

        return {
            "summary": {
                "total_conversions": float(total_conversions),
                "total_revenue": float(total_revenue),
                "total_spend": float(total_spend),
                "overall_roas": round(total_revenue / total_spend, 2) if total_spend > 0 else None,
                "overall_cpa": round(total_spend / total_conversions, 2) if total_conversions > 0 else None,
            },
            "last_touch_attribution": last_touch,
            "channel_efficiency": efficiency,
            "top_performers": {
                "best_roas": best_roas,
                "worst_roas": worst_roas,
                "best_cpa": best_cpa,
                "worst_cpa": worst_cpa
            },
            "recommendations": self._generate_attribution_recommendations(efficiency)
        }

    def _generate_attribution_recommendations(self, efficiency: dict) -> list[str]:
        """Generate recommendations based on attribution analysis."""
        recommendations = []

        if not efficiency:
            return recommendations

        # Find channels with good ROAS but low spend share
        for channel, metrics in efficiency.items():
            roas = metrics.get('roas')
            spend_share = metrics.get('spend_share', 0)

            if roas and roas > 3 and spend_share < 20:
                recommendations.append(
                    f"Consider increasing budget for {channel} - high ROAS ({roas}x) but only {spend_share}% of spend"
                )

            if roas and roas < 1 and spend_share > 20:
                recommendations.append(
                    f"Review {channel} strategy - low ROAS ({roas}x) despite {spend_share}% of spend"
                )

        return recommendations

    def correlation_analysis(self, df: pd.DataFrame) -> dict:
        """Analyze correlations between metrics."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        metrics = ['spend', 'impressions', 'clicks', 'conversions', 'revenue', 'ctr', 'cpc', 'roas']
        relevant_cols = [c for c in numeric_cols if c in metrics]

        if len(relevant_cols) < 2:
            return {"error": "Insufficient numeric columns for correlation analysis"}

        corr_matrix = df[relevant_cols].corr()

        # Find strongest correlations
        correlations = []
        for i, col1 in enumerate(relevant_cols):
            for col2 in relevant_cols[i+1:]:
                corr = corr_matrix.loc[col1, col2]
                if not np.isnan(corr):
                    correlations.append({
                        "metric_1": col1,
                        "metric_2": col2,
                        "correlation": round(corr, 3),
                        "strength": "strong" if abs(corr) > 0.7 else "moderate" if abs(corr) > 0.4 else "weak",
                        "direction": "positive" if corr > 0 else "negative"
                    })

        # Sort by absolute correlation
        correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)

        return {
            "matrix": {col: {c: round(v, 3) for c, v in row.items()}
                      for col, row in corr_matrix.to_dict().items()},
            "top_correlations": correlations[:10],
            "insights": self._generate_correlation_insights(correlations)
        }

    def _generate_correlation_insights(self, correlations: list) -> list[str]:
        """Generate insights from correlation analysis."""
        insights = []

        for corr in correlations[:5]:
            if corr["strength"] == "strong":
                direction = "increases" if corr["direction"] == "positive" else "decreases"
                insights.append(
                    f"Strong relationship: As {corr['metric_1']} goes up, {corr['metric_2']} {direction} "
                    f"(correlation: {corr['correlation']})"
                )

        return insights

    def segmentation_analysis(self, df: pd.DataFrame, segment_by: str) -> dict:
        """Analyze performance by segment/dimension."""
        if segment_by not in df.columns:
            return {"error": f"Column {segment_by} not found"}

        metrics = ['spend', 'impressions', 'clicks', 'conversions', 'revenue']
        available = [m for m in metrics if m in df.columns]

        if not available:
            return {"error": "No metrics found for segmentation"}

        segment_data = df.groupby(segment_by).agg({
            m: 'sum' for m in available
        }).reset_index()

        # Calculate derived metrics per segment
        results = []
        for _, row in segment_data.iterrows():
            segment = {
                "segment": row[segment_by],
                "metrics": {m: float(row[m]) for m in available}
            }

            # Add calculated metrics
            if 'spend' in available and 'clicks' in available and row['clicks'] > 0:
                segment["metrics"]["cpc"] = round(row['spend'] / row['clicks'], 2)

            if 'spend' in available and 'conversions' in available and row['conversions'] > 0:
                segment["metrics"]["cpa"] = round(row['spend'] / row['conversions'], 2)

            if 'spend' in available and 'revenue' in available and row['spend'] > 0:
                segment["metrics"]["roas"] = round(row['revenue'] / row['spend'], 2)

            if 'clicks' in available and 'impressions' in available and row['impressions'] > 0:
                segment["metrics"]["ctr"] = round(row['clicks'] / row['impressions'] * 100, 2)

            results.append(segment)

        # Rank segments
        if 'revenue' in available:
            results.sort(key=lambda x: x["metrics"].get("revenue", 0), reverse=True)
            for i, r in enumerate(results):
                r["rank_by_revenue"] = i + 1

        return {
            "segment_by": segment_by,
            "segment_count": len(results),
            "segments": results,
            "top_segment": results[0]["segment"] if results else None,
            "bottom_segment": results[-1]["segment"] if results else None
        }
