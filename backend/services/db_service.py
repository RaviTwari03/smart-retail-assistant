from sqlalchemy.orm import Session

from database import SessionLocal

from db_models import (
    ForecastRecord,
    ChatHistory
)

# Create DB Session
def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()

# Save Forecast
def save_forecast(
    predicted_sales,
    sales_trend
):

    db = SessionLocal()

    record = ForecastRecord(
        predicted_sales=predicted_sales,
        sales_trend=sales_trend
    )

    db.add(record)

    db.commit()

    db.refresh(record)

    db.close()

    return record

# Save Chat
def save_chat(query, response):

    db = SessionLocal()

    chat = ChatHistory(
        query=query,
        response=response
    )

    db.add(chat)

    db.commit()

    db.refresh(chat)

    db.close()

    return chat