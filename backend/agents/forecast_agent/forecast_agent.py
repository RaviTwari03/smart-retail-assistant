"""
Forecast Agent
==============
Interprets Prophet sales forecast data and generates
human-readable insights for the retail assistant.
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


def forecast_agent() -> Dict:
    """
    Run the forecast pipeline and return structured insights.

    Returns:
        Dict with forecast data, trend direction, and narrative summary.
    """
    logger.info("Forecast agent running")

    try:
        from services.forecast_service import predict_future_sales

        predictions = predict_future_sales(periods=7)

        if not predictions:
            return {
                "status": "error",
                "message": "No forecast data available"
            }

        # Determine trend
        first_val = predictions[0]["yhat"]
        last_val = predictions[-1]["yhat"]
        change_pct = ((last_val - first_val) / first_val) * 100

        if change_pct > 2:
            trend = "Upward 📈"
        elif change_pct < -2:
            trend = "Downward 📉"
        else:
            trend = "Stable ➡️"

        peak = max(predictions, key=lambda x: x["yhat"])
        low = min(predictions, key=lambda x: x["yhat"])

        summary = (
            f"7-day sales forecast shows a {trend} trend. "
            f"Peak sales expected on {peak['ds']} "
            f"(${peak['yhat']:,.0f}). "
            f"Lowest on {low['ds']} (${low['yhat']:,.0f}). "
            f"Overall change: {change_pct:+.1f}%."
        )

        return {
            "status": "success",
            "trend": trend,
            "forecast": predictions,
            "summary": summary,
            "peak_day": peak["ds"],
            "peak_sales": peak["yhat"]
        }

    except Exception as e:
        logger.error(f"Forecast agent error: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": str(e)
        }
