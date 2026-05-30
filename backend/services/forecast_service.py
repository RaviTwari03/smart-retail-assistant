"""
Forecast Service
================
Real Prophet-based sales forecasting for the Smart Retail Assistant.

Uses the Walmart dataset to train a Prophet model and predict
future weekly sales. Falls back to a pre-trained pickle model
if available, otherwise trains on-the-fly.

Architecture:
    Walmart.csv (Raw data)
        ↓ Preprocess (Date → ds, Weekly_Sales → y)
        ↓ Prophet model.fit(df)
        ↓ model.predict(future_dates)
        ↓ Return 7-day forecast
"""

import logging
import os
import pickle
from pathlib import Path
from typing import List, Dict

import pandas as pd

logger = logging.getLogger(__name__)

# =========================
# PATHS
# =========================

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_PATH = BASE_DIR.parent / "data" / "Raw" / "Walmart.csv"

MODEL_PATH = BASE_DIR / "models" / "forecast_model.pkl"

FORECAST_PERIODS = 7


# =========================
# TRAIN OR LOAD MODEL
# =========================

def _load_or_train_model():
    """
    Load a pre-trained Prophet model from disk, or train a new one
    from the Walmart dataset if no saved model exists.

    Returns:
        Prophet: Fitted Prophet model instance.

    Raises:
        FileNotFoundError: If neither model nor dataset is available.
    """
    from prophet import Prophet

    # Try loading saved model first
    if MODEL_PATH.exists():
        logger.info(f"Loading pre-trained forecast model from {MODEL_PATH}")
        with open(MODEL_PATH, "rb") as f:
            return pickle.load(f)

    # Train from dataset
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Walmart dataset not found at {DATASET_PATH}. "
            "Cannot train forecast model."
        )

    logger.info(f"Training new Prophet model from {DATASET_PATH}")

    df = pd.read_csv(DATASET_PATH)

    # Parse dates
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)

    # Aggregate weekly sales across all stores (sum per date)
    df_agg = (
        df.groupby("Date")["Weekly_Sales"]
        .sum()
        .reset_index()
        .rename(columns={"Date": "ds", "Weekly_Sales": "y"})
    )

    df_agg = df_agg.sort_values("ds").reset_index(drop=True)

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.05
    )

    model.fit(df_agg)

    # Persist model for future use
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    logger.info(f"Prophet model trained and saved to {MODEL_PATH}")

    return model


# =========================
# PREDICT FUTURE SALES
# =========================

def predict_future_sales(periods: int = FORECAST_PERIODS) -> List[Dict]:
    """
    Generate future sales forecasts using Prophet.

    Args:
        periods (int): Number of future days to forecast. Default: 7.

    Returns:
        List[Dict]: List of {"ds": "YYYY-MM-DD", "yhat": float,
                             "yhat_lower": float, "yhat_upper": float}

    Raises:
        Exception: If model loading/training or prediction fails.
    """
    logger.info(f"Generating {periods}-day sales forecast using Prophet")

    model = _load_or_train_model()

    # Create future dataframe
    future = model.make_future_dataframe(periods=periods, freq="W")

    # Predict
    forecast = model.predict(future)

    # Return only future predictions (last `periods` rows)
    result_df = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(periods)

    # Convert to JSON-serializable format
    result = []
    for _, row in result_df.iterrows():
        result.append({
            "ds": str(row["ds"].date()),
            "yhat": round(float(row["yhat"]), 2),
            "yhat_lower": round(float(row["yhat_lower"]), 2),
            "yhat_upper": round(float(row["yhat_upper"]), 2)
        })

    logger.info(f"Forecast generated: {len(result)} periods")

    return result
