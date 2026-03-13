"""
Data Cleaning Service

Handles messy, inconsistent marketing data by:
- Normalizing column names to standard marketing terms
- Cleaning and parsing dates in various formats
- Standardizing categorical values (channels, sources, campaigns)
- Handling missing values intelligently
- Detecting and fixing data type issues
- Currency normalization
- Outlier detection and flagging
"""

import pandas as pd
import numpy as np
import re
from typing import Optional, Tuple
from datetime import datetime


# Standard marketing column mappings
COLUMN_MAPPINGS = {
    # Date columns
    "date": ["date", "day", "report_date", "reporting_date", "dt", "timestamp", "time", "period"],

    # Dimension columns
    "campaign": ["campaign", "campaign_name", "campaign_id", "campaigns", "camp", "campaign name"],
    "ad_group": ["ad_group", "adgroup", "ad group", "ad_group_name", "adset", "ad_set", "ad set"],
    "ad": ["ad", "ad_name", "ad_id", "creative", "creative_name", "ad name"],
    "channel": ["channel", "platform", "network", "advertising_channel", "ad_channel", "media_channel"],
    "source": ["source", "traffic_source", "utm_source", "src", "referrer"],
    "medium": ["medium", "utm_medium", "marketing_medium", "med"],
    "device": ["device", "device_type", "device_category", "platform_device"],
    "country": ["country", "geo", "geography", "region", "location", "country_code"],
    "audience": ["audience", "audience_name", "segment", "targeting", "audience_segment"],

    # Metric columns - engagement
    "impressions": ["impressions", "imps", "impression", "views", "ad_impressions", "total_impressions"],
    "clicks": ["clicks", "click", "total_clicks", "ad_clicks", "link_clicks"],
    "sessions": ["sessions", "visits", "session", "website_sessions"],
    "pageviews": ["pageviews", "page_views", "pages", "page views"],
    "bounce_rate": ["bounce_rate", "bounces", "bounce", "bounce rate"],

    # Metric columns - conversions
    "conversions": ["conversions", "conversion", "conv", "converts", "total_conversions", "purchases", "orders", "leads", "signups", "sign_ups"],
    "conversion_value": ["conversion_value", "conv_value", "purchase_value", "order_value", "value"],

    # Metric columns - cost
    "spend": ["spend", "cost", "ad_spend", "amount_spent", "total_cost", "media_cost", "ad_cost", "budget_spent"],
    "cpc": ["cpc", "cost_per_click", "avg_cpc", "average_cpc"],
    "cpm": ["cpm", "cost_per_mille", "cost_per_thousand"],
    "cpa": ["cpa", "cost_per_acquisition", "cost_per_conversion", "cost_per_action"],

    # Metric columns - revenue
    "revenue": ["revenue", "total_revenue", "sales", "income", "gross_revenue", "total_sales"],
    "roas": ["roas", "return_on_ad_spend", "return on ad spend"],

    # Rates
    "ctr": ["ctr", "click_through_rate", "clickthrough_rate", "click rate"],
    "conversion_rate": ["conversion_rate", "conv_rate", "cvr", "cr"],
}

# Channel name standardization
CHANNEL_MAPPINGS = {
    "google_ads": ["google ads", "google", "adwords", "google adwords", "gads", "google ppc", "search ads"],
    "facebook": ["facebook", "fb", "facebook ads", "meta", "facebook/instagram"],
    "instagram": ["instagram", "ig", "insta", "instagram ads"],
    "tiktok": ["tiktok", "tik tok", "tiktok ads", "tt"],
    "linkedin": ["linkedin", "li", "linkedin ads"],
    "twitter": ["twitter", "x", "twitter ads"],
    "pinterest": ["pinterest", "pin", "pinterest ads"],
    "snapchat": ["snapchat", "snap", "snapchat ads"],
    "youtube": ["youtube", "yt", "youtube ads"],
    "display": ["display", "gdn", "display network", "programmatic"],
    "email": ["email", "mail", "email marketing", "newsletter"],
    "organic_search": ["organic", "seo", "organic search", "natural search"],
    "direct": ["direct", "direct traffic", "(direct)"],
    "referral": ["referral", "referrals", "affiliate"],
}


class DataCleaner:
    """Service for cleaning and normalizing messy marketing data."""

    def __init__(self):
        self.cleaning_report = []

    def clean_dataframe(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
        """
        Clean and normalize a DataFrame.

        Returns:
            Tuple of (cleaned DataFrame, cleaning report)
        """
        self.cleaning_report = []
        original_shape = df.shape

        # Step 1: Normalize column names
        df = self._normalize_column_names(df)

        # Step 2: Clean and parse dates
        df = self._parse_dates(df)

        # Step 3: Standardize categorical values
        df = self._standardize_categories(df)

        # Step 4: Clean numeric columns
        df = self._clean_numeric_columns(df)

        # Step 5: Handle missing values
        df = self._handle_missing_values(df)

        # Step 6: Calculate derived metrics if possible
        df = self._calculate_derived_metrics(df)

        # Step 7: Detect and flag outliers
        outlier_info = self._detect_outliers(df)

        report = {
            "original_shape": original_shape,
            "cleaned_shape": df.shape,
            "actions_taken": self.cleaning_report,
            "outliers_detected": outlier_info,
            "columns_mapped": list(df.columns),
        }

        return df, report

    def _normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names to standard marketing terms."""
        df = df.copy()

        # First, clean up column names (lowercase, remove special chars)
        df.columns = [self._clean_column_name(col) for col in df.columns]

        # Map to standard names
        rename_map = {}
        for standard_name, variations in COLUMN_MAPPINGS.items():
            for col in df.columns:
                if col in variations or any(v in col for v in variations):
                    if col not in rename_map:
                        rename_map[col] = standard_name
                        break

        if rename_map:
            df = df.rename(columns=rename_map)
            self.cleaning_report.append(f"Normalized {len(rename_map)} column names: {rename_map}")

        return df

    def _clean_column_name(self, name: str) -> str:
        """Clean a single column name."""
        # Convert to lowercase
        name = str(name).lower().strip()
        # Replace spaces and special chars with underscores
        name = re.sub(r'[^\w]', '_', name)
        # Remove multiple underscores
        name = re.sub(r'_+', '_', name)
        # Remove leading/trailing underscores
        name = name.strip('_')
        return name

    def _parse_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Parse and standardize date columns."""
        df = df.copy()

        date_columns = [col for col in df.columns if 'date' in col.lower() or col in ['date', 'day', 'period']]

        for col in date_columns:
            if col in df.columns:
                try:
                    # Try multiple date formats
                    df[col] = pd.to_datetime(df[col], infer_datetime_format=True, errors='coerce')
                    valid_dates = df[col].notna().sum()
                    self.cleaning_report.append(f"Parsed {valid_dates} dates in '{col}'")
                except Exception as e:
                    self.cleaning_report.append(f"Could not parse dates in '{col}': {str(e)}")

        return df

    def _standardize_categories(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize categorical values like channel names."""
        df = df.copy()

        # Standardize channel names
        if 'channel' in df.columns:
            df['channel'] = df['channel'].apply(self._standardize_channel)
            self.cleaning_report.append("Standardized channel names")

        # Standardize source names
        if 'source' in df.columns:
            df['source'] = df['source'].apply(self._standardize_channel)
            self.cleaning_report.append("Standardized source names")

        # Clean campaign names (trim whitespace, title case)
        if 'campaign' in df.columns:
            df['campaign'] = df['campaign'].astype(str).str.strip()
            self.cleaning_report.append("Cleaned campaign names")

        return df

    def _standardize_channel(self, value: str) -> str:
        """Standardize a channel/source value."""
        if pd.isna(value):
            return "unknown"

        value_lower = str(value).lower().strip()

        for standard_name, variations in CHANNEL_MAPPINGS.items():
            if value_lower in variations or any(v in value_lower for v in variations):
                return standard_name

        return value_lower

    def _clean_numeric_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean numeric columns - remove currency symbols, commas, etc."""
        df = df.copy()

        numeric_indicators = ['spend', 'cost', 'revenue', 'impressions', 'clicks', 'conversions',
                            'cpc', 'cpm', 'cpa', 'roas', 'ctr', 'rate', 'value']

        for col in df.columns:
            if any(ind in col.lower() for ind in numeric_indicators):
                if df[col].dtype == object:
                    try:
                        # Remove currency symbols and commas
                        df[col] = df[col].astype(str).str.replace(r'[$,£€¥]', '', regex=True)
                        df[col] = df[col].str.replace(r'%', '', regex=True)
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                        self.cleaning_report.append(f"Cleaned numeric values in '{col}'")
                    except Exception:
                        pass

        return df

    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values intelligently based on column type."""
        df = df.copy()
        missing_before = df.isnull().sum().sum()

        for col in df.columns:
            if df[col].isnull().any():
                # For metrics, fill with 0
                if any(m in col.lower() for m in ['spend', 'cost', 'clicks', 'impressions', 'conversions', 'revenue']):
                    df[col] = df[col].fillna(0)
                # For rates, leave as NaN (will be calculated)
                elif any(r in col.lower() for r in ['rate', 'ctr', 'cpc', 'cpm', 'roas']):
                    pass
                # For categories, fill with 'unknown'
                elif df[col].dtype == object:
                    df[col] = df[col].fillna('unknown')

        missing_after = df.isnull().sum().sum()
        if missing_before > missing_after:
            self.cleaning_report.append(f"Handled {missing_before - missing_after} missing values")

        return df

    def _calculate_derived_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate standard marketing metrics if source data is available."""
        df = df.copy()

        # CTR = clicks / impressions * 100
        if 'clicks' in df.columns and 'impressions' in df.columns and 'ctr' not in df.columns:
            df['ctr'] = np.where(df['impressions'] > 0,
                                 (df['clicks'] / df['impressions'] * 100).round(2),
                                 0)
            self.cleaning_report.append("Calculated CTR (click-through rate)")

        # CPC = spend / clicks
        if 'spend' in df.columns and 'clicks' in df.columns and 'cpc' not in df.columns:
            df['cpc'] = np.where(df['clicks'] > 0,
                                 (df['spend'] / df['clicks']).round(2),
                                 0)
            self.cleaning_report.append("Calculated CPC (cost per click)")

        # CPM = spend / impressions * 1000
        if 'spend' in df.columns and 'impressions' in df.columns and 'cpm' not in df.columns:
            df['cpm'] = np.where(df['impressions'] > 0,
                                 (df['spend'] / df['impressions'] * 1000).round(2),
                                 0)
            self.cleaning_report.append("Calculated CPM (cost per mille)")

        # CPA = spend / conversions
        if 'spend' in df.columns and 'conversions' in df.columns and 'cpa' not in df.columns:
            df['cpa'] = np.where(df['conversions'] > 0,
                                 (df['spend'] / df['conversions']).round(2),
                                 0)
            self.cleaning_report.append("Calculated CPA (cost per acquisition)")

        # ROAS = revenue / spend
        if 'revenue' in df.columns and 'spend' in df.columns and 'roas' not in df.columns:
            df['roas'] = np.where(df['spend'] > 0,
                                  (df['revenue'] / df['spend']).round(2),
                                  0)
            self.cleaning_report.append("Calculated ROAS (return on ad spend)")

        # Conversion Rate = conversions / clicks * 100
        if 'conversions' in df.columns and 'clicks' in df.columns and 'conversion_rate' not in df.columns:
            df['conversion_rate'] = np.where(df['clicks'] > 0,
                                             (df['conversions'] / df['clicks'] * 100).round(2),
                                             0)
            self.cleaning_report.append("Calculated conversion rate")

        return df

    def _detect_outliers(self, df: pd.DataFrame) -> dict:
        """Detect outliers in numeric columns using IQR method."""
        outliers = {}

        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            if df[col].nunique() > 10:  # Only check columns with enough variety
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1

                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                outlier_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
                outlier_count = outlier_mask.sum()

                if outlier_count > 0:
                    outliers[col] = {
                        "count": int(outlier_count),
                        "percentage": round(outlier_count / len(df) * 100, 1),
                        "lower_bound": round(lower_bound, 2),
                        "upper_bound": round(upper_bound, 2)
                    }

        if outliers:
            self.cleaning_report.append(f"Detected outliers in {len(outliers)} columns")

        return outliers
