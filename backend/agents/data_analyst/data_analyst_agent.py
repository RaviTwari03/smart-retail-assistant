"""
Data Analyst Agent
==================
Answers analytical questions about retail sales data
using the Walmart dataset. Provides store-level insights,
anomaly summaries, and trend analysis.
"""

import logging
from pathlib import Path
from typing import Dict

import pandas as pd

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATASET_PATH = BASE_DIR.parent / "data" / "Raw" / "Walmart.csv"


def _load_data() -> pd.DataFrame:
    """Load and preprocess the Walmart sales dataset."""
    df = pd.read_csv(DATASET_PATH)
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)
    return df


def data_analyst_agent(query: str = "") -> Dict:
    """
    Analyze retail sales data and return key business insights.

    Args:
        query (str): Optional natural language query (used for context).

    Returns:
        Dict with analytics insights including top stores, revenue,
        trends, and anomaly summary.
    """
    logger.info(f"Data analyst agent running for query: {query}")

    try:
        df = _load_data()

        # Top 5 stores by total sales
        top_stores = (
            df.groupby("Store")["Weekly_Sales"]
            .sum()
            .sort_values(ascending=False)
            .head(5)
            .reset_index()
        )

        top_stores_list = [
            {"store": int(row["Store"]), "total_sales": round(float(row["Weekly_Sales"]), 2)}
            for _, row in top_stores.iterrows()
        ]

        # Overall metrics
        total_revenue = round(float(df["Weekly_Sales"].sum()), 2)
        avg_weekly_sales = round(float(df["Weekly_Sales"].mean()), 2)
        total_stores = int(df["Store"].nunique())

        # Holiday vs non-holiday sales
        if "Holiday_Flag" in df.columns:
            holiday_avg = round(float(df[df["Holiday_Flag"] == 1]["Weekly_Sales"].mean()), 2)
            non_holiday_avg = round(float(df[df["Holiday_Flag"] == 0]["Weekly_Sales"].mean()), 2)
            holiday_lift_pct = round(((holiday_avg - non_holiday_avg) / non_holiday_avg) * 100, 1)
        else:
            holiday_avg = None
            non_holiday_avg = None
            holiday_lift_pct = None

        # Sales trend (compare first half vs second half)
        df_sorted = df.sort_values("Date")
        mid = len(df_sorted) // 2
        first_half_avg = round(float(df_sorted.iloc[:mid]["Weekly_Sales"].mean()), 2)
        second_half_avg = round(float(df_sorted.iloc[mid:]["Weekly_Sales"].mean()), 2)
        trend = "Upward" if second_half_avg > first_half_avg else "Downward"

        summary = (
            f"Analyzed {total_stores} stores with total revenue of "
            f"${total_revenue:,.0f}. Average weekly sales: ${avg_weekly_sales:,.0f}. "
            f"Overall sales trend is {trend}. "
            f"Top performing store: Store {top_stores_list[0]['store']}."
        )

        return {
            "status": "success",
            "total_revenue": total_revenue,
            "avg_weekly_sales": avg_weekly_sales,
            "total_stores": total_stores,
            "top_stores": top_stores_list,
            "sales_trend": trend,
            "holiday_avg_sales": holiday_avg,
            "non_holiday_avg_sales": non_holiday_avg,
            "holiday_lift_pct": holiday_lift_pct,
            "summary": summary
        }

    except Exception as e:
        logger.error(f"Data analyst agent error: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": str(e)
        }
