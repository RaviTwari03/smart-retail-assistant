import pandas as pd

df = pd.read_csv("/Users/ravitiwari/Downloads/Walmart.csv")

print(df.head())

df.dropna(inplace=True)

df.to_csv("/Users/ravitiwari/Downloads/cleaned_sales.csv", index=False)

print("Data cleaned successfully")