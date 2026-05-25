import pandas as pd


def preprocess_data(file_path):

    # Load dataset
    df = pd.read_csv(file_path)

    # Remove null values
    df.dropna(inplace=True)

    # Convert Date column properly
    df["Date"] = pd.to_datetime(
        df["Date"],
        dayfirst=True
    )

    # Sort by date
    df = df.sort_values("Date")

    return df