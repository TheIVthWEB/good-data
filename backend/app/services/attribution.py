"""
Multi-Touch Attribution Service

Supports multiple attribution models:
- Last-touch: 100% credit to final touchpoint
- First-touch: 100% credit to first touchpoint
- Linear: Equal credit across all touchpoints
- Position-based (U-shaped): 40% first, 40% last, 20% split middle
- Time-decay: More credit to recent touchpoints
- W-shaped: 30% first, 30% lead creation, 30% last, 10% middle
- Data-driven: Statistical analysis of conversion patterns
"""

import pandas as pd
import numpy as np
from typing import Optional
from collections import defaultdict
from datetime import datetime, timedelta


class AttributionModels:
    """Multi-touch attribution modeling."""

    def __init__(self, decay_rate: float = 0.7):
        """
        Args:
            decay_rate: For time-decay model, how much credit decays per step (0.7 = 30% decay)
        """
        self.decay_rate = decay_rate

    def attribute_journeys(self, df: pd.DataFrame,
                          user_col: str = 'user_id',
                          timestamp_col: str = 'timestamp',
                          channel_col: str = 'channel',
                          conversion_col: str = 'converted',
                          revenue_col: str = None) -> dict:
        """
        Run all attribution models on user journey data.

        Expected DataFrame columns:
        - user_id: Unique user identifier
        - timestamp: When the touchpoint occurred
        - channel: Marketing channel/source
        - converted: Boolean or 0/1 indicating conversion
        - revenue (optional): Revenue from conversion

        Returns attribution results for all models.
        """
        required = [user_col, timestamp_col, channel_col, conversion_col]
        missing = [c for c in required if c not in df.columns]
        if missing:
            return {"error": f"Missing required columns: {missing}"}

        # Parse and sort by user and time
        df = df.copy()
        df[timestamp_col] = pd.to_datetime(df[timestamp_col])
        df = df.sort_values([user_col, timestamp_col])

        # Build user journeys
        journeys = self._build_journeys(df, user_col, timestamp_col, channel_col,
                                        conversion_col, revenue_col)

        if not journeys['converting']:
            return {"error": "No converting journeys found in data"}

        # Run all attribution models
        results = {
            "journey_stats": {
                "total_users": len(set(df[user_col])),
                "converting_journeys": len(journeys['converting']),
                "non_converting_journeys": len(journeys['non_converting']),
                "conversion_rate": round(len(journeys['converting']) /
                    (len(journeys['converting']) + len(journeys['non_converting'])) * 100, 2),
                "avg_touchpoints_converting": round(np.mean([len(j['touchpoints'])
                    for j in journeys['converting']]), 2),
                "avg_touchpoints_non_converting": round(np.mean([len(j['touchpoints'])
                    for j in journeys['non_converting']]), 2) if journeys['non_converting'] else 0,
            },
            "models": {}
        }

        # Calculate each attribution model
        models = {
            "last_touch": self._last_touch,
            "first_touch": self._first_touch,
            "linear": self._linear,
            "position_based": self._position_based,
            "time_decay": self._time_decay,
            "w_shaped": self._w_shaped,
        }

        for model_name, model_func in models.items():
            results["models"][model_name] = model_func(journeys['converting'])

        # Add model comparison
        results["model_comparison"] = self._compare_models(results["models"])

        # Add channel insights
        results["channel_insights"] = self._generate_channel_insights(
            results["models"], journeys
        )

        return results

    def _build_journeys(self, df: pd.DataFrame, user_col: str, timestamp_col: str,
                       channel_col: str, conversion_col: str, revenue_col: str) -> dict:
        """Build journey sequences from raw touchpoint data."""
        journeys = {'converting': [], 'non_converting': []}

        for user_id, user_df in df.groupby(user_col):
            touchpoints = []
            converted = False
            revenue = 0

            for _, row in user_df.iterrows():
                touchpoints.append({
                    'channel': row[channel_col],
                    'timestamp': row[timestamp_col],
                })

                if row[conversion_col]:
                    converted = True
                    if revenue_col and revenue_col in df.columns:
                        revenue = row[revenue_col]

            journey = {
                'user_id': user_id,
                'touchpoints': touchpoints,
                'channels': [t['channel'] for t in touchpoints],
                'revenue': revenue,
            }

            if converted:
                journeys['converting'].append(journey)
            else:
                journeys['non_converting'].append(journey)

        return journeys

    def _last_touch(self, journeys: list) -> dict:
        """Last-touch attribution: 100% credit to final touchpoint."""
        credit = defaultdict(lambda: {'conversions': 0, 'revenue': 0})

        for journey in journeys:
            last_channel = journey['channels'][-1]
            credit[last_channel]['conversions'] += 1
            credit[last_channel]['revenue'] += journey['revenue']

        return self._format_attribution_result(credit, "last_touch", journeys)

    def _first_touch(self, journeys: list) -> dict:
        """First-touch attribution: 100% credit to first touchpoint."""
        credit = defaultdict(lambda: {'conversions': 0, 'revenue': 0})

        for journey in journeys:
            first_channel = journey['channels'][0]
            credit[first_channel]['conversions'] += 1
            credit[first_channel]['revenue'] += journey['revenue']

        return self._format_attribution_result(credit, "first_touch", journeys)

    def _linear(self, journeys: list) -> dict:
        """Linear attribution: Equal credit across all touchpoints."""
        credit = defaultdict(lambda: {'conversions': 0, 'revenue': 0})

        for journey in journeys:
            channels = journey['channels']
            n = len(channels)
            credit_per_touch = 1.0 / n
            revenue_per_touch = journey['revenue'] / n

            for channel in channels:
                credit[channel]['conversions'] += credit_per_touch
                credit[channel]['revenue'] += revenue_per_touch

        return self._format_attribution_result(credit, "linear", journeys)

    def _position_based(self, journeys: list) -> dict:
        """
        Position-based (U-shaped) attribution:
        - First touch: 40%
        - Last touch: 40%
        - Middle touches: Split remaining 20%
        """
        credit = defaultdict(lambda: {'conversions': 0, 'revenue': 0})

        for journey in journeys:
            channels = journey['channels']
            n = len(channels)

            if n == 1:
                credit[channels[0]]['conversions'] += 1
                credit[channels[0]]['revenue'] += journey['revenue']
            elif n == 2:
                credit[channels[0]]['conversions'] += 0.5
                credit[channels[0]]['revenue'] += journey['revenue'] * 0.5
                credit[channels[1]]['conversions'] += 0.5
                credit[channels[1]]['revenue'] += journey['revenue'] * 0.5
            else:
                # First and last get 40% each
                credit[channels[0]]['conversions'] += 0.4
                credit[channels[0]]['revenue'] += journey['revenue'] * 0.4
                credit[channels[-1]]['conversions'] += 0.4
                credit[channels[-1]]['revenue'] += journey['revenue'] * 0.4

                # Middle channels split 20%
                middle_credit = 0.2 / (n - 2)
                middle_revenue = journey['revenue'] * 0.2 / (n - 2)
                for channel in channels[1:-1]:
                    credit[channel]['conversions'] += middle_credit
                    credit[channel]['revenue'] += middle_revenue

        return self._format_attribution_result(credit, "position_based", journeys)

    def _time_decay(self, journeys: list) -> dict:
        """
        Time-decay attribution: More recent touchpoints get more credit.
        Uses exponential decay from last touchpoint.
        """
        credit = defaultdict(lambda: {'conversions': 0, 'revenue': 0})

        for journey in journeys:
            channels = journey['channels']
            n = len(channels)

            # Calculate decay weights (most recent = highest weight)
            weights = [self.decay_rate ** (n - 1 - i) for i in range(n)]
            total_weight = sum(weights)

            # Normalize weights
            normalized_weights = [w / total_weight for w in weights]

            for i, channel in enumerate(channels):
                credit[channel]['conversions'] += normalized_weights[i]
                credit[channel]['revenue'] += journey['revenue'] * normalized_weights[i]

        return self._format_attribution_result(credit, "time_decay", journeys)

    def _w_shaped(self, journeys: list) -> dict:
        """
        W-shaped attribution (for B2B):
        - First touch: 30%
        - Lead creation (middle): 30%
        - Last touch (opportunity): 30%
        - Remaining touches: 10%
        """
        credit = defaultdict(lambda: {'conversions': 0, 'revenue': 0})

        for journey in journeys:
            channels = journey['channels']
            n = len(channels)

            if n == 1:
                credit[channels[0]]['conversions'] += 1
                credit[channels[0]]['revenue'] += journey['revenue']
            elif n == 2:
                credit[channels[0]]['conversions'] += 0.5
                credit[channels[0]]['revenue'] += journey['revenue'] * 0.5
                credit[channels[1]]['conversions'] += 0.5
                credit[channels[1]]['revenue'] += journey['revenue'] * 0.5
            elif n == 3:
                for channel in channels:
                    credit[channel]['conversions'] += 1/3
                    credit[channel]['revenue'] += journey['revenue'] / 3
            else:
                # First, middle, last get 30% each
                mid_idx = n // 2
                key_positions = [0, mid_idx, n-1]

                credit[channels[0]]['conversions'] += 0.3
                credit[channels[0]]['revenue'] += journey['revenue'] * 0.3
                credit[channels[mid_idx]]['conversions'] += 0.3
                credit[channels[mid_idx]]['revenue'] += journey['revenue'] * 0.3
                credit[channels[-1]]['conversions'] += 0.3
                credit[channels[-1]]['revenue'] += journey['revenue'] * 0.3

                # Remaining touches split 10%
                other_indices = [i for i in range(n) if i not in key_positions]
                if other_indices:
                    other_credit = 0.1 / len(other_indices)
                    other_revenue = journey['revenue'] * 0.1 / len(other_indices)
                    for i in other_indices:
                        credit[channels[i]]['conversions'] += other_credit
                        credit[channels[i]]['revenue'] += other_revenue

        return self._format_attribution_result(credit, "w_shaped", journeys)

    def _format_attribution_result(self, credit: dict, model_name: str, journeys: list) -> dict:
        """Format attribution results consistently."""
        total_conversions = len(journeys)
        total_revenue = sum(j['revenue'] for j in journeys)

        channels = []
        for channel, values in credit.items():
            channels.append({
                "channel": channel,
                "attributed_conversions": round(values['conversions'], 2),
                "conversion_share": round(values['conversions'] / total_conversions * 100, 2),
                "attributed_revenue": round(values['revenue'], 2),
                "revenue_share": round(values['revenue'] / total_revenue * 100, 2) if total_revenue > 0 else 0,
            })

        # Sort by attributed conversions
        channels.sort(key=lambda x: x['attributed_conversions'], reverse=True)

        return {
            "model": model_name,
            "total_conversions": total_conversions,
            "total_revenue": total_revenue,
            "channels": channels,
        }

    def _compare_models(self, models: dict) -> dict:
        """Compare attribution across models to identify discrepancies."""
        comparison = {}

        # Get all channels
        all_channels = set()
        for model_result in models.values():
            for ch in model_result['channels']:
                all_channels.add(ch['channel'])

        # Build comparison matrix
        for channel in all_channels:
            comparison[channel] = {}
            for model_name, model_result in models.items():
                channel_data = next(
                    (c for c in model_result['channels'] if c['channel'] == channel),
                    None
                )
                if channel_data:
                    comparison[channel][model_name] = {
                        "conversions": channel_data['attributed_conversions'],
                        "share": channel_data['conversion_share']
                    }
                else:
                    comparison[channel][model_name] = {"conversions": 0, "share": 0}

        # Find channels with biggest model discrepancy
        discrepancies = []
        for channel, model_values in comparison.items():
            shares = [v['share'] for v in model_values.values()]
            if shares:
                discrepancy = max(shares) - min(shares)
                discrepancies.append({
                    "channel": channel,
                    "max_share": max(shares),
                    "min_share": min(shares),
                    "discrepancy": round(discrepancy, 2),
                    "interpretation": self._interpret_discrepancy(channel, model_values)
                })

        discrepancies.sort(key=lambda x: x['discrepancy'], reverse=True)

        return {
            "by_channel": comparison,
            "largest_discrepancies": discrepancies[:5],
            "recommendation": self._model_recommendation(discrepancies)
        }

    def _interpret_discrepancy(self, channel: str, model_values: dict) -> str:
        """Interpret why a channel shows different attribution across models."""
        first = model_values.get('first_touch', {}).get('share', 0)
        last = model_values.get('last_touch', {}).get('share', 0)

        if first > last * 1.5:
            return f"{channel} is primarily an awareness/discovery channel (introduces users)"
        elif last > first * 1.5:
            return f"{channel} is primarily a conversion/closing channel (final touchpoint)"
        else:
            return f"{channel} appears throughout the funnel (both discovery and conversion)"

    def _model_recommendation(self, discrepancies: list) -> str:
        """Recommend which model to use based on data patterns."""
        if not discrepancies:
            return "Insufficient data to recommend a model"

        avg_discrepancy = np.mean([d['discrepancy'] for d in discrepancies])

        if avg_discrepancy < 10:
            return "Low discrepancy across models. Any model works; use linear for simplicity."
        elif avg_discrepancy < 25:
            return "Moderate discrepancy. Consider position-based for balanced attribution."
        else:
            return "High discrepancy. Channels have distinct roles. Use position-based or time-decay to capture funnel dynamics."

    def _generate_channel_insights(self, models: dict, journeys: dict) -> list:
        """Generate actionable insights about channels."""
        insights = []

        first = {c['channel']: c['share'] for c in models['first_touch']['channels']}
        last = {c['channel']: c['share'] for c in models['last_touch']['channels']}

        for channel in first.keys():
            f_share = first.get(channel, 0)
            l_share = last.get(channel, 0)

            if f_share > l_share * 2:
                insights.append({
                    "channel": channel,
                    "role": "awareness",
                    "insight": f"{channel} starts journeys but rarely closes them. Pair with retargeting channels.",
                    "first_touch_share": f_share,
                    "last_touch_share": l_share
                })
            elif l_share > f_share * 2:
                insights.append({
                    "channel": channel,
                    "role": "conversion",
                    "insight": f"{channel} closes deals but doesn't drive awareness. Ensure upstream channels feed it.",
                    "first_touch_share": f_share,
                    "last_touch_share": l_share
                })
            elif f_share > 15 and l_share > 15:
                insights.append({
                    "channel": channel,
                    "role": "full_funnel",
                    "insight": f"{channel} works across the entire funnel. High-value channel for scaling.",
                    "first_touch_share": f_share,
                    "last_touch_share": l_share
                })

        return insights

    def attribute_aggregated_data(self, df: pd.DataFrame,
                                  channel_col: str = 'channel',
                                  spend_col: str = 'spend',
                                  conversions_col: str = 'conversions',
                                  revenue_col: str = 'revenue') -> dict:
        """
        Attribution analysis for aggregated channel data (no user journeys).

        This provides last-touch equivalent plus efficiency metrics.
        For multi-touch attribution, user journey data is required.
        """
        if channel_col not in df.columns:
            return {"error": f"Channel column '{channel_col}' not found"}

        available_metrics = []
        for col in [spend_col, conversions_col, revenue_col]:
            if col in df.columns:
                available_metrics.append(col)

        if not available_metrics:
            return {"error": "No metrics columns found"}

        # Aggregate by channel
        agg_dict = {m: 'sum' for m in available_metrics}
        channel_data = df.groupby(channel_col).agg(agg_dict).reset_index()

        totals = {m: channel_data[m].sum() for m in available_metrics}

        channels = []
        for _, row in channel_data.iterrows():
            channel_result = {
                "channel": row[channel_col],
            }

            if conversions_col in available_metrics:
                channel_result["conversions"] = float(row[conversions_col])
                channel_result["conversion_share"] = round(
                    row[conversions_col] / totals[conversions_col] * 100, 2
                ) if totals[conversions_col] > 0 else 0

            if spend_col in available_metrics:
                channel_result["spend"] = float(row[spend_col])
                channel_result["spend_share"] = round(
                    row[spend_col] / totals[spend_col] * 100, 2
                ) if totals[spend_col] > 0 else 0

            if revenue_col in available_metrics:
                channel_result["revenue"] = float(row[revenue_col])
                channel_result["revenue_share"] = round(
                    row[revenue_col] / totals[revenue_col] * 100, 2
                ) if totals[revenue_col] > 0 else 0

            # Efficiency metrics
            if spend_col in available_metrics and conversions_col in available_metrics:
                channel_result["cpa"] = round(
                    row[spend_col] / row[conversions_col], 2
                ) if row[conversions_col] > 0 else None

            if spend_col in available_metrics and revenue_col in available_metrics:
                channel_result["roas"] = round(
                    row[revenue_col] / row[spend_col], 2
                ) if row[spend_col] > 0 else None

            channels.append(channel_result)

        # Sort by conversions
        if conversions_col in available_metrics:
            channels.sort(key=lambda x: x.get('conversions', 0), reverse=True)

        return {
            "model": "last_touch_aggregated",
            "note": "Aggregated data only supports last-touch attribution. Upload user journey data for multi-touch models.",
            "totals": totals,
            "channels": channels,
            "recommendations": self._aggregated_recommendations(channels)
        }

    def _aggregated_recommendations(self, channels: list) -> list:
        """Generate recommendations from aggregated attribution."""
        recommendations = []

        for ch in channels:
            roas = ch.get('roas')
            spend_share = ch.get('spend_share', 0)
            conversion_share = ch.get('conversion_share', 0)

            if roas and roas > 3 and spend_share < conversion_share:
                recommendations.append({
                    "channel": ch['channel'],
                    "action": "increase_budget",
                    "reason": f"High ROAS ({roas}x) with room to scale"
                })
            elif roas and roas < 1 and spend_share > 15:
                recommendations.append({
                    "channel": ch['channel'],
                    "action": "reduce_or_optimize",
                    "reason": f"ROAS below 1x ({roas}x) with significant spend"
                })

        return recommendations
