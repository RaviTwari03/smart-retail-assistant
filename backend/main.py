import os
import uvicorn

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# =========================
# Database Imports
# =========================

from database import engine, Base, SessionLocal
from db_models import ChatHistory

from services.db_service import (
    save_forecast,
    save_chat
)

# =========================
# FastAPI Initialization
# =========================

Base.metadata.create_all(bind=engine)

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

    try:
        from services.forecast_service import predict_future_sales

        predictions = predict_future_sales()

        latest_prediction = predictions[-1]["yhat"]

        trend = "Upward"

        return {
            "status": "success",
            "forecast": predictions
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }


# =========================
# Anomaly Detection API
# =========================

@app.post("/detect-anomaly")
def anomaly_detection(data: SalesData):

    try:
        from services.anomaly_service import detect_anomalies

        results = detect_anomalies(data.sales)

        return {
            "status": "success",
            "results": results
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }


# =========================
# RAG Document Search API
# =========================

@app.post("/search-documents")
def search_docs(data: QueryRequest):

    try:
        from services.rag_service import search_documents

        results = search_documents(data.query)

        return {
            "status": "success",
            "query": data.query,
            "results": results
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }


# =========================
# Customer Support Agent API
# =========================

@app.post("/customer-support")
def customer_support(data: QueryRequest):

    try:
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

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }


# =========================
# Multi-Agent Retail Assistant API
# =========================

@app.post("/retail-assistant")
def retail_assistant(data: OrchestratorRequest):

    try:
        from agents.orchestrator import orchestrator

        result = orchestrator(
            query=data.query,
            stock=data.stock
        )

        return {
            "status": "success",
            "data": result
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }


# =========================
# Chat History API
# =========================

@app.get("/chat-history")
def get_chat_history():

    try:

        db = SessionLocal()

        chats = db.query(ChatHistory).all()

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

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }


# =========================
# Azure Bot Endpoint
# =========================

@app.post("/api/messages")
async def bot_messages(request: Request):

    try:

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

    except Exception as e:

        return JSONResponse(
            content={
                "status": "error",
                "message": str(e)
            },
            status_code=500
        )


# =========================
# Startup Entry Point
# =========================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8000))

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port
    )