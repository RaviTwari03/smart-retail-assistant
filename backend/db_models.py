from sqlalchemy import Column, Integer, String, Float

from database import Base

class ForecastRecord(Base):

    __tablename__ = "forecast_records"

    id = Column(Integer, primary_key=True, index=True)

    predicted_sales = Column(Float)

    sales_trend = Column(String)

class ChatHistory(Base):

    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)

    query = Column(String)

    response = Column(String)