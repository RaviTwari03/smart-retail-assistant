from prophet import Prophet
import pandas as pd
import pickle

def train_forecast_model(df):

    forecast_df = df[["Date", "Weekly_Sales"]]

    forecast_df.columns = ["ds", "y"]

    model = Prophet()

    model.fit(forecast_df)

    with open("models/forecast_model.pkl", "wb") as f:
        pickle.dump(model, f)

    return model