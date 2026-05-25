from sklearn.ensemble import IsolationForest
import pickle

def train_anomaly_model(df):

    anomaly_df = df[["Weekly_Sales"]]

    model = IsolationForest(
        contamination=0.02,
        random_state=42
    )

    model.fit(anomaly_df)

    with open("models/anomaly_model.pkl", "wb") as f:
        pickle.dump(model, f)

    return model