# import pandas as pd
# from sklearn.linear_model import LinearRegression
# from sklearn.model_selection import train_test_split
# import pickle

# df = pd.read_csv("/Users/ravitiwari/Downloads/cleaned_sales.csv")

# X = df[["Store"]]
# y = df["Weekly_Sales"]

# X_train, X_test, y_train, y_test = train_test_split(
#     X, y, test_size=0.2
# )

# model = LinearRegression()

# model.fit(X_train, y_train)

# pickle.dump(model, open("forecast_model.pkl", "wb"))

# print("Model trained successfully")

from utils.preprocess import preprocess_data
from models.forecast_model import train_forecast_model
from models.anomaly_model import train_anomaly_model

# Load and preprocess dataset
df = preprocess_data("../data/Raw/Walmart.csv")

# Train forecasting model
train_forecast_model(df)

# Train anomaly detection model
train_anomaly_model(df)

print("All models trained successfully")