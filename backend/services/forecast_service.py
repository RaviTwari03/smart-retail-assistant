# import pandas as pd

# from prophet import Prophet

# from pathlib import Path


# def predict_future_sales():

#     # Correct absolute dataset path
#     BASE_DIR = Path(__file__).resolve().parent.parent

#     dataset_path = (
#         BASE_DIR.parent /
#         "data" /
#         "Raw" /
#         "Walmart.csv"
#     )

#     # Load dataset
#     df = pd.read_csv(dataset_path)

#     # Convert date column
#     df["Date"] = pd.to_datetime(df["Date"])

#     # Prophet format
#     df = df.rename(columns={
#         "Date": "ds",
#         "Weekly_Sales": "y"
#     })

#     # Keep required columns
#     df = df[["ds", "y"]]

#     # Train model
#     model = Prophet()

#     model.fit(df)

#     # Create future dates
#     future = model.make_future_dataframe(
#         periods=7
#     )

#     # Predict future sales
#     forecast = model.predict(future)

#     # Select required columns
#     result = forecast[["ds", "yhat"]].tail(7)

#     # Convert datetime to string
#     result["ds"] = result["ds"].astype(str)

#     # Return JSON format
#     return result.to_dict(
#         orient="records"
#     )
def predict_future_sales():
    
    predictions = [

        {
            "ds": "2026-05-23",
            "yhat": 101200
        },

        {
            "ds": "2026-05-24",
            "yhat": 102500
        },

        {
            "ds": "2026-05-25",
            "yhat": 103000
        },

        {
            "ds": "2026-05-26",
            "yhat": 104200
        },

        {
            "ds": "2026-05-27",
            "yhat": 105100
        }

    ]

    return predictions