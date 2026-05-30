"""
Anomaly Detection Service
=========================
Uses a pre-trained IsolationForest model to detect unusual
weekly sales values.

The model is loaded lazily on first use so that:
- Tests can run without the pickle file present
- The app starts even if the model hasn't been trained yet
"""

import logging
import os
import pickle
from pathlib import Path
from typing import List, Dict, Union

import pandas as pd

logger = logging.getLogger(__name__)

# Path relative to the backend root
MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "anomaly_model.pkl"

# Lazy-loaded model — None until first call to detect_anomalies()
_model = None


def _load_model():
    """
    Load the anomaly model from disk on first use.

    Returns:
        Trained IsolationForest model.

    Raises:
        FileNotFoundError: If the model pickle does not exist.
    """
    global _model

    if _model is not None:
        return _model

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Anomaly model not found at '{MODEL_PATH}'. "
            "Run train_model.py to generate it."
        )

    logger.info(f"Loading anomaly model from {MODEL_PATH}")

    with open(MODEL_PATH, "rb") as f:
        _model = pickle.load(f)

    return _model


def detect_anomalies(values: List[float]) -> Union[List[Dict], Dict]:
    """
    Detect anomalies in a list of weekly sales values.

    Args:
        values: List of weekly sales figures.

    Returns:
        List of {"sales": float, "is_anomaly": bool} dicts,
        or {"error": str} on failure.
    """
    try:
        model = _load_model()

        df = pd.DataFrame({"Weekly_Sales": values})

        predictions = model.predict(df)

        return [
            {
                "sales": float(value),
                "is_anomaly": bool(pred == -1)
            }
            for value, pred in zip(values, predictions)
        ]

    except FileNotFoundError as e:
        logger.error(str(e))
        return {"error": str(e)}

    except Exception as e:
        logger.error(f"Anomaly detection failed: {str(e)}", exc_info=True)
        return {"error": str(e)}
