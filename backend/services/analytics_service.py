"""
Analytics Service
=================
Computes Power BI-friendly KPI metrics from the Walmart dataset
and live application data (forecast, chat history, blob storage).

All functions return flat, denormalised dicts / lists that Power BI
can consume directly via the Web connector without any M-query transforms.

Endpoints served:
    GET /analytics/revenue        → revenue KPIs + weekly trend series
    GET /analytics/inventory      → stock-level metrics + store breakdown
    GET /analytics/forecast       → Prophet forecast + confidence bands
    GET /analytics/agent-insights → agent usage, RAG stats, chat history
"""

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from database import SessionLocal
from services.anomaly_service import detect_anomalies
from services.blob_service import list_documents
from services.forecast_service import predict_future_sales

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR.parent / "data" / "Raw" / "Walmart.csv"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_walmart() -> pd.DataFrame:
    """Load and lightly preprocess the Walmart CSV."""
    df = pd.read_csv(DATASET_PATH)
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)
    df["Weekly_Sales"] = df["Weekly_Sales"].astype(float)
    return df


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# 1. Revenue Analytics
# ---------------------------------------------------------------------------

def get_revenue_analytics() -> Dict[str, Any]:
    """
    Power BI Revenue Dashboard data.

    Returns
    -------
    {
        "kpis": {
            "total_revenue": float,          # all-time sum
            "avg_weekly_revenue": float,      # mean weekly sales across all stores
            "peak_weekly_revenue": float,     # single highest weekly total
            "peak_week_date": str,            # date of that peak
            "total_stores": int,
            "total_weeks": int,
            "holiday_revenue": float,         # sum on holiday weeks
            "non_holiday_revenue": float,
            "holiday_lift_pct": float         # % uplift on holidays
        },
        "weekly_trend": [                     # for line chart
            {"date": "YYYY-MM-DD", "total_sales": float, "is_holiday": bool},
            ...
        ],
        "top_stores": [                       # for bar chart
            {"store_id": int, "total_sales": float, "rank": int},
            ...
        ],
        "monthly_summary": [                  # for column chart
            {"month": "YYYY-MM", "total_sales": float, "avg_sales": float},
            ...
        ],
        "generated_at": str
    }
    """
    logger.info("Computing revenue analytics")
    df = _load_walmart()

    # ── KPIs ──────────────────────────────────────────────────────────────
    total_revenue = round(float(df["Weekly_Sales"].sum()), 2)
    avg_weekly = round(float(df.groupby("Date")["Weekly_Sales"].sum().mean()), 2)

    weekly_totals = df.groupby("Date")["Weekly_Sales"].sum()
    peak_date = weekly_totals.idxmax()
    peak_value = round(float(weekly_totals.max()), 2)

    holiday_rev = round(float(df[df["Holiday_Flag"] == 1]["Weekly_Sales"].sum()), 2)
    non_holiday_rev = round(float(df[df["Holiday_Flag"] == 0]["Weekly_Sales"].sum()), 2)
    holiday_lift = round(
        ((df[df["Holiday_Flag"] == 1]["Weekly_Sales"].mean() -
          df[df["Holiday_Flag"] == 0]["Weekly_Sales"].mean()) /
         df[df["Holiday_Flag"] == 0]["Weekly_Sales"].mean()) * 100, 2
    )

    # ── Weekly trend series ───────────────────────────────────────────────
    weekly = (
        df.groupby(["Date", "Holiday_Flag"])["Weekly_Sales"]
        .sum()
        .reset_index()
        .sort_values("Date")
    )
    weekly_trend = [
        {
            "date": str(row["Date"].date()),
            "total_sales": round(float(row["Weekly_Sales"]), 2),
            "is_holiday": bool(row["Holiday_Flag"] == 1)
        }
        for _, row in weekly.iterrows()
    ]

    # ── Top 10 stores ─────────────────────────────────────────────────────
    store_totals = (
        df.groupby("Store")["Weekly_Sales"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    top_stores = [
        {
            "store_id": int(row["Store"]),
            "total_sales": round(float(row["Weekly_Sales"]), 2),
            "rank": rank + 1
        }
        for rank, (_, row) in enumerate(store_totals.iterrows())
    ]

    # ── Monthly summary ───────────────────────────────────────────────────
    df["month"] = df["Date"].dt.to_period("M").astype(str)
    monthly = df.groupby("month")["Weekly_Sales"].agg(["sum", "mean"]).reset_index()
    monthly_summary = [
        {
            "month": row["month"],
            "total_sales": round(float(row["sum"]), 2),
            "avg_sales": round(float(row["mean"]), 2)
        }
        for _, row in monthly.iterrows()
    ]

    return {
        "kpis": {
            "total_revenue": total_revenue,
            "avg_weekly_revenue": avg_weekly,
            "peak_weekly_revenue": peak_value,
            "peak_week_date": str(peak_date.date()),
            "total_stores": int(df["Store"].nunique()),
            "total_weeks": int(df["Date"].nunique()),
            "holiday_revenue": holiday_rev,
            "non_holiday_revenue": non_holiday_rev,
            "holiday_lift_pct": holiday_lift
        },
        "weekly_trend": weekly_trend,
        "top_stores": top_stores,
        "monthly_summary": monthly_summary,
        "generated_at": _now_iso()
    }


# ---------------------------------------------------------------------------
# 2. Inventory Analytics
# ---------------------------------------------------------------------------

def get_inventory_analytics() -> Dict[str, Any]:
    """
    Power BI Inventory Dashboard data.

    Returns
    -------
    {
        "kpis": {
            "total_stores": int,
            "critical_stock_stores": int,     # simulated from sales variance
            "warning_stock_stores": int,
            "stable_stock_stores": int,
            "avg_unemployment": float,        # economic context
            "avg_fuel_price": float,
            "avg_cpi": float
        },
        "store_inventory_status": [           # for table / map visual
            {
                "store_id": int,
                "avg_weekly_sales": float,
                "sales_volatility": float,    # std dev
                "stock_status": str,          # Critical / Warning / Stable
                "alert_level": int            # 3=critical, 2=warning, 1=stable
            },
            ...
        ],
        "anomaly_summary": {
            "total_weeks_analysed": int,
            "anomaly_weeks": int,
            "anomaly_rate_pct": float
        },
        "economic_indicators": [              # for line chart
            {"date": str, "fuel_price": float, "cpi": float, "unemployment": float},
            ...
        ],
        "generated_at": str
    }
    """
    logger.info("Computing inventory analytics")
    df = _load_walmart()

    # ── Per-store status based on sales volatility ────────────────────────
    store_stats = (
        df.groupby("Store")["Weekly_Sales"]
        .agg(["mean", "std"])
        .reset_index()
        .rename(columns={"mean": "avg_weekly_sales", "std": "sales_volatility"})
    )
    store_stats["sales_volatility"] = store_stats["sales_volatility"].fillna(0)

    # Classify: high volatility → critical, medium → warning, low → stable
    p33 = store_stats["sales_volatility"].quantile(0.33)
    p66 = store_stats["sales_volatility"].quantile(0.66)

    def _classify(vol: float) -> tuple:
        if vol >= p66:
            return "Critical", 3
        elif vol >= p33:
            return "Warning", 2
        return "Stable", 1

    store_inventory = []
    for _, row in store_stats.iterrows():
        status, level = _classify(row["sales_volatility"])
        store_inventory.append({
            "store_id": int(row["Store"]),
            "avg_weekly_sales": round(float(row["avg_weekly_sales"]), 2),
            "sales_volatility": round(float(row["sales_volatility"]), 2),
            "stock_status": status,
            "alert_level": level
        })

    critical = sum(1 for s in store_inventory if s["stock_status"] == "Critical")
    warning  = sum(1 for s in store_inventory if s["stock_status"] == "Warning")
    stable   = sum(1 for s in store_inventory if s["stock_status"] == "Stable")

    # ── Anomaly summary (IsolationForest on aggregated weekly sales) ──────
    weekly_sales = df.groupby("Date")["Weekly_Sales"].sum().values.tolist()
    anomaly_weeks = 0
    try:
        anomaly_results = detect_anomalies(weekly_sales)
        if isinstance(anomaly_results, list):
            anomaly_weeks = sum(1 for r in anomaly_results if r.get("is_anomaly"))
    except Exception as e:
        logger.warning(f"Anomaly detection skipped: {e}")

    total_weeks = len(weekly_sales)
    anomaly_rate = round((anomaly_weeks / total_weeks) * 100, 2) if total_weeks else 0

    # ── Economic indicators time series ───────────────────────────────────
    eco = (
        df.groupby("Date")[["Fuel_Price", "CPI", "Unemployment"]]
        .mean()
        .reset_index()
        .sort_values("Date")
    )
    economic_indicators = [
        {
            "date": str(row["Date"].date()),
            "fuel_price": round(float(row["Fuel_Price"]), 3),
            "cpi": round(float(row["CPI"]), 3),
            "unemployment": round(float(row["Unemployment"]), 3)
        }
        for _, row in eco.iterrows()
    ]

    return {
        "kpis": {
            "total_stores": int(df["Store"].nunique()),
            "critical_stock_stores": critical,
            "warning_stock_stores": warning,
            "stable_stock_stores": stable,
            "avg_unemployment": round(float(df["Unemployment"].mean()), 3),
            "avg_fuel_price": round(float(df["Fuel_Price"].mean()), 3),
            "avg_cpi": round(float(df["CPI"].mean()), 3)
        },
        "store_inventory_status": store_inventory,
        "anomaly_summary": {
            "total_weeks_analysed": total_weeks,
            "anomaly_weeks": anomaly_weeks,
            "anomaly_rate_pct": anomaly_rate
        },
        "economic_indicators": economic_indicators,
        "generated_at": _now_iso()
    }


# ---------------------------------------------------------------------------
# 3. Forecast Analytics
# ---------------------------------------------------------------------------

def get_forecast_analytics() -> Dict[str, Any]:
    """
    Power BI Forecast Dashboard data.

    Returns
    -------
    {
        "kpis": {
            "forecast_periods": int,
            "next_week_forecast": float,
            "peak_forecast_value": float,
            "peak_forecast_date": str,
            "min_forecast_value": float,
            "min_forecast_date": str,
            "avg_forecast_value": float,
            "trend_direction": str,          # Upward / Downward / Stable
            "trend_change_pct": float
        },
        "forecast_series": [                 # for line + confidence band chart
            {
                "date": str,
                "forecast": float,
                "lower_bound": float,
                "upper_bound": float,
                "confidence_width": float
            },
            ...
        ],
        "historical_vs_forecast": [          # last 8 historical + 7 forecast
            {"date": str, "value": float, "type": "historical" | "forecast"},
            ...
        ],
        "generated_at": str
    }
    """
    logger.info("Computing forecast analytics")

    from services.forecast_service import predict_future_sales
    predictions = predict_future_sales(periods=7)
    values = [p["yhat"] for p in predictions]
    peak   = max(predictions, key=lambda x: x["yhat"])
    low    = min(predictions, key=lambda x: x["yhat"])
    trend_change = round(((values[-1] - values[0]) / values[0]) * 100, 2) if values[0] else 0

    if trend_change > 2:
        trend_dir = "Upward"
    elif trend_change < -2:
        trend_dir = "Downward"
    else:
        trend_dir = "Stable"

    # ── Forecast series ───────────────────────────────────────────────────
    forecast_series = [
        {
            "date": p["ds"],
            "forecast": p["yhat"],
            "lower_bound": p["yhat_lower"],
            "upper_bound": p["yhat_upper"],
            "confidence_width": round(p["yhat_upper"] - p["yhat_lower"], 2)
        }
        for p in predictions
    ]

    # ── Historical (last 8 weeks) + forecast combined ─────────────────────
    df = _load_walmart()
    hist = (
        df.groupby("Date")["Weekly_Sales"]
        .sum()
        .reset_index()
        .sort_values("Date")
        .tail(8)
    )
    historical_vs_forecast = [
        {
            "date": str(row["Date"].date()),
            "value": round(float(row["Weekly_Sales"]), 2),
            "type": "historical"
        }
        for _, row in hist.iterrows()
    ] + [
        {
            "date": p["ds"],
            "value": p["yhat"],
            "type": "forecast"
        }
        for p in predictions
    ]

    return {
        "kpis": {
            "forecast_periods": len(predictions),
            "next_week_forecast": round(values[0], 2),
            "peak_forecast_value": round(peak["yhat"], 2),
            "peak_forecast_date": peak["ds"],
            "min_forecast_value": round(low["yhat"], 2),
            "min_forecast_date": low["ds"],
            "avg_forecast_value": round(sum(values) / len(values), 2),
            "trend_direction": trend_dir,
            "trend_change_pct": trend_change
        },
        "forecast_series": forecast_series,
        "historical_vs_forecast": historical_vs_forecast,
        "generated_at": _now_iso()
    }


# ---------------------------------------------------------------------------
# 4. Agent Insights Analytics
# ---------------------------------------------------------------------------

def get_agent_insights() -> Dict[str, Any]:
    """
    Power BI Agent Usage Dashboard data.

    Returns
    -------
    {
        "kpis": {
            "total_chats": int,
            "knowledge_base_documents": int,
            "vector_db_exists": bool,
            "agents_available": int,
            "rag_enabled": bool
        },
        "chat_history": [                    # for table visual
            {"id": int, "query": str, "response_preview": str},
            ...
        ],
        "agent_registry": [                  # for card / table visual
            {"agent_name": str, "type": str, "status": str, "description": str},
            ...
        ],
        "knowledge_base_documents": [        # for table visual
            {"document_name": str, "type": str},
            ...
        ],
        "rag_pipeline_status": {
            "azure_blob_connected": bool,
            "vector_db_ready": bool,
            "embedding_model": str,
            "chunk_size": int,
            "chunk_overlap": int,
            "similarity_k": int
        },
        "generated_at": str
    }
    """
    logger.info("Computing agent insights")

    # ── Chat history from PostgreSQL ──────────────────────────────────────
    chat_history = []
    total_chats = 0
    try:
        from database import SessionLocal
        from db_models import ChatHistory
        db = SessionLocal()
        chats = db.query(ChatHistory).order_by(ChatHistory.id.desc()).limit(50).all()
        total_chats = db.query(ChatHistory).count()
        db.close()
        chat_history = [
            {
                "id": c.id,
                "query": c.query,
                "response_preview": (c.response[:120] + "...") if c.response and len(c.response) > 120 else (c.response or "")
            }
            for c in chats
        ]
    except Exception as e:
        logger.warning(f"Could not load chat history: {e}")

    # ── Knowledge base documents from Azure Blob ──────────────────────────
    kb_docs = []
    blob_connected = False
    try:
        from services.blob_service import list_documents
        doc_names = list_documents()
        blob_connected = True
        kb_docs = [
            {
                "document_name": name,
                "type": name.rsplit(".", 1)[-1].upper() if "." in name else "UNKNOWN"
            }
            for name in doc_names
        ]
    except Exception as e:
        logger.warning(f"Could not list blob documents: {e}")

    # ── Vector DB status ──────────────────────────────────────────────────
    import os
    vector_db_ready = os.path.exists("./vector_db")

    # ── Agent registry ────────────────────────────────────────────────────
    agent_registry = [
        {
            "agent_name": "Customer Support Agent",
            "type": "RAG + LLM",
            "status": "Active",
            "description": "Answers customer queries using knowledge base + GPT-3.5-turbo"
        },
        {
            "agent_name": "Inventory Agent",
            "type": "Rule-Based",
            "status": "Active",
            "description": "Classifies stock levels: Critical / Warning / Stable"
        },
        {
            "agent_name": "Forecast Agent",
            "type": "ML (Prophet)",
            "status": "Active",
            "description": "Generates 7-day sales forecast with trend analysis"
        },
        {
            "agent_name": "Data Analyst Agent",
            "type": "Analytics",
            "status": "Active",
            "description": "Analyses Walmart dataset for store-level insights"
        },
        {
            "agent_name": "Document Search Agent",
            "type": "RAG",
            "status": "Active",
            "description": "Returns raw knowledge base chunks for a given query"
        }
    ]

    return {
        "kpis": {
            "total_chats": total_chats,
            "knowledge_base_documents": len(kb_docs),
            "vector_db_exists": vector_db_ready,
            "agents_available": len(agent_registry),
            "rag_enabled": blob_connected and vector_db_ready
        },
        "chat_history": chat_history,
        "agent_registry": agent_registry,
        "knowledge_base_documents": kb_docs,
        "rag_pipeline_status": {
            "azure_blob_connected": blob_connected,
            "vector_db_ready": vector_db_ready,
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "chunk_size": 300,
            "chunk_overlap": 50,
            "similarity_k": 3
        },
        "generated_at": _now_iso()
    }
