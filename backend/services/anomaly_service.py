import pickle
import pandas as pd

# Load trained anomaly model
with open("models/anomaly_model.pkl", "rb") as f:
    model = pickle.load(f)


def detect_anomalies(values):

    try:

        # Convert input into DataFrame
        df = pd.DataFrame({
            "Weekly_Sales": values
        })

        # Predict anomalies
        predictions = model.predict(df)

        results = []

        for value, pred in zip(values, predictions):

            results.append({
                "sales": float(value),
                "is_anomaly": bool(pred == -1)
            })

        return results

    except Exception as e:

        return {
            "error": str(e)
        }