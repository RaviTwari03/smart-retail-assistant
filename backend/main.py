from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from pydantic import BaseModel

from fastapi.middleware.cors import CORSMiddleware

# =========================
# Database Imports
# =========================

from database import SessionLocal

from db_models import ChatHistory

from services.db_service import (
    save_forecast,
    save_chat
)

# =========================
# FastAPI Initialization
# =========================

app = FastAPI(
    title="Smart Retail Assistant",
    description="AI-powered retail analytics and assistant platform",
    version="1.0.0"
)

# =========================
# CORS Middleware
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# Request Models
# =========================

class SalesData(BaseModel):

    sales: list[float]


class QueryRequest(BaseModel):

    query: str


class OrchestratorRequest(BaseModel):

    query: str

    stock: int

# =========================
# Root Endpoint
# =========================

@app.get("/")
def home():

    return {
        "message": "Smart Retail Assistant API Running Successfully"
    }

# =========================
# Health Check Endpoint
# =========================

@app.get("/health")
def health_check():

    return {
        "status": "healthy"
    }

# =========================
# Dashboard Metrics API
# =========================

@app.get("/dashboard-metrics")
def dashboard_metrics():

    return {
        "total_revenue": 250000,
        "inventory_alerts": 9,
        "sales_trend": "Upward"
    }

# =========================
# Forecast API
# =========================

@app.get("/forecast")
def forecast_sales():

    from services.forecast_service import (
        predict_future_sales
    )

    predictions = predict_future_sales()

    latest_prediction = predictions[-1]["yhat"]

    trend = "Upward"

    # save_forecast(
    #     predicted_sales=latest_prediction,
    #     sales_trend=trend
    # )

    return {
        "status": "success",
        "forecast": predictions
    }

# =========================
# Anomaly Detection API
# =========================

@app.post("/detect-anomaly")
def anomaly_detection(data: SalesData):

    from services.anomaly_service import (
        detect_anomalies
    )

    results = detect_anomalies(data.sales)

    return {
        "status": "success",
        "results": results
    }

# =========================
# RAG Document Search API
# =========================

@app.post("/search-documents")
def search_docs(data: QueryRequest):

    from services.rag_service import (
        search_documents
    )

    results = search_documents(data.query)

    return {
        "status": "success",
        "query": data.query,
        "results": results
    }

# =========================
# Customer Support Agent API
# =========================

@app.post("/customer-support")
def customer_support(data: QueryRequest):

    from agents.customer_support.support_agent import (
        customer_support_agent
    )

    response = customer_support_agent(
        data.query
    )

    save_chat(
        query=data.query,
        response=response
    )

    return {
        "status": "success",
        "response": response
    }

# =========================
# Multi-Agent Retail Assistant API
# =========================

@app.post("/retail-assistant")
def retail_assistant(data: OrchestratorRequest):

    from agents.orchestrator import (
        orchestrator
    )

    result = orchestrator(
        query=data.query,
        stock=data.stock
    )

    return {
        "status": "success",
        "data": result
    }

# =========================
# Chat History API
# =========================

@app.get("/chat-history")
def get_chat_history():

    db = SessionLocal()

    chats = db.query(
        ChatHistory
    ).all()

    result = []

    for chat in chats:

        result.append({

            "id": chat.id,

            "query": chat.query,

            "response": chat.response
        })

    db.close()

    return {
        "status": "success",
        "history": result
    }

# =========================
# Azure Bot Endpoint
# =========================

# =========================
# Azure Bot Endpoint
# =========================

# @app.post("/api/messages")
# async def bot_messages(request: Request):

#     try:

#         body = await request.json()

#         print("===================================")
#         print("Incoming Azure Bot Message:")
#         print(body)
#         print("===================================")

#         user_message = body.get("text", "Hello")

#         response_body = {
#             "type": "message",
#             "text": f"You said: {user_message}"
#         }

#         return JSONResponse(
#             content=response_body,
#             status_code=200
#         )

#     except Exception as e:

#         print("ERROR:", str(e))

#         return JSONResponse(
#             content={
#                 "type": "message",
#                 "text": "Bot Error Occurred"
#             },
#             status_code=200
#         )

@app.post("/api/messages")
async def bot_messages(request: Request):

    body = await request.json()

    print("===================================")
    print("Incoming Azure Bot Message:")
    print(body)
    print("===================================")

    user_message = body.get("text", "")

    return {
        "type": "message",
        "text": f"Hello Ravi 👋 You said: {user_message}"
    }