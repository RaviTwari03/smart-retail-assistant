

import logging
import os
import tempfile

import uvicorn
from fastapi import FastAPI, File, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ─────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Database
# ─────────────────────────────────────────────────────────────

from database import engine, Base, SessionLocal
from db_models import ChatHistory
from services.db_service import save_forecast, save_chat

Base.metadata.create_all(bind=engine)

# ─────────────────────────────────────────────────────────────
# FastAPI app
# ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="Smart Retail Assistant",
    description="AI-powered retail analytics and assistant platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────
# Request models
# ─────────────────────────────────────────────────────────────

class SalesData(BaseModel):
    sales: list[float]

class QueryRequest(BaseModel):
    query: str

class OrchestratorRequest(BaseModel):
    query: str
    stock: int


# ─────────────────────────────────────────────────────────────
# Startup: auto-build vector DB
# ─────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event() -> None:
    logger.info("=" * 60)
    logger.info("Smart Retail Assistant — startup")
    logger.info("=" * 60)

    try:
        from services.rag_service import vector_db_exists, create_vector_db
        if vector_db_exists():
            logger.info("Vector database already exists — skipping auto-build")
        else:
            logger.info("Vector database not found — building from Azure Blob Storage...")
            result = create_vector_db()
            logger.info(f"Startup vector DB build result: {result}")
    except Exception as exc:
        logger.warning(f"Startup vector DB build failed (non-fatal): {exc}", exc_info=True)

    logger.info("Startup complete — API is ready")


# ─────────────────────────────────────────────────────────────
# Core endpoints
# ─────────────────────────────────────────────────────────────

@app.get("/")
def home():
    return {"message": "Smart Retail Assistant API Running Successfully"}


@app.get("/health")
def health_check():
    from services.rag_service import vector_db_exists
    return {
        "status": "healthy",
        "vector_db_ready": vector_db_exists(),
    }


@app.get("/dashboard-metrics")
def dashboard_metrics():
    return {
        "total_revenue": 250000,
        "inventory_alerts": 9,
        "sales_trend": "Upward",
    }


# ─────────────────────────────────────────────────────────────
# Forecast
# ─────────────────────────────────────────────────────────────

@app.get("/forecast")
def forecast_sales():
    try:
        from services.forecast_service import predict_future_sales
        predictions = predict_future_sales()
        return {"status": "success", "forecast": predictions}
    except Exception as exc:
        logger.error(f"Forecast error: {exc}", exc_info=True)
        return {"status": "error", "message": str(exc)}


# ─────────────────────────────────────────────────────────────
# Anomaly detection
# ─────────────────────────────────────────────────────────────

@app.post("/detect-anomaly")
def anomaly_detection(data: SalesData):
    try:
        from services.anomaly_service import detect_anomalies
        results = detect_anomalies(data.sales)
        return {"status": "success", "results": results}
    except Exception as exc:
        logger.error(f"Anomaly detection error: {exc}", exc_info=True)
        return {"status": "error", "message": str(exc)}


# ─────────────────────────────────────────────────────────────
# RAG search
# ─────────────────────────────────────────────────────────────

@app.post("/search-documents")
def search_docs(data: QueryRequest):
    try:
        from services.rag_service import search_documents
        results = search_documents(data.query)
        return {"status": "success", "query": data.query, "results": results}
    except Exception as exc:
        logger.error(f"Search error: {exc}", exc_info=True)
        return {"status": "error", "message": str(exc)}


# ─────────────────────────────────────────────────────────────
# Customer support agent
# ─────────────────────────────────────────────────────────────

@app.post("/customer-support")
def customer_support(data: QueryRequest):
    try:
        from agents.customer_support.support_agent import customer_support_agent
        response = customer_support_agent(data.query)
        save_chat(query=data.query, response=response)
        return {"status": "success", "response": response}
    except Exception as exc:
        logger.error(f"Customer support error: {exc}", exc_info=True)
        return {"status": "error", "message": str(exc)}


# ─────────────────────────────────────────────────────────────
# Multi-agent orchestrator
# ─────────────────────────────────────────────────────────────

@app.post("/retail-assistant")
def retail_assistant(data: OrchestratorRequest):
    try:
        from agents.orchestrator import orchestrator
        result = orchestrator(query=data.query, stock=data.stock)
        return {"status": "success", "data": result}
    except Exception as exc:
        logger.error(f"Retail assistant error: {exc}", exc_info=True)
        return {"status": "error", "message": str(exc)}


# ─────────────────────────────────────────────────────────────
# Chat history
# ─────────────────────────────────────────────────────────────

@app.get("/chat-history")
def get_chat_history():
    try:
        db = SessionLocal()
        chats = db.query(ChatHistory).all()
        result = [{"id": c.id, "query": c.query, "response": c.response} for c in chats]
        db.close()
        return {"status": "success", "history": result}
    except Exception as exc:
        logger.error(f"Chat history error: {exc}", exc_info=True)
        return {"status": "error", "message": str(exc)}


# ─────────────────────────────────────────────────────────────
# Azure Bot (Dummy Endpoint)
# ─────────────────────────────────────────────────────────────

@app.post("/api/messages")
async def bot_messages(request: Request):
    return {"status": "ok", "message": "Bot is currently in direct-response mode."}


# ─────────────────────────────────────────────────────────────
# Blob Storage — List
# ─────────────────────────────────────────────────────────────

@app.get("/blob-documents")
def list_blob_documents():
    try:
        from services.blob_service import list_documents
        return {"status": "success", "documents": list_documents()}
    except Exception as exc:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(exc)})


# ─────────────────────────────────────────────────────────────
# Blob Storage — Upload / Delete
# ─────────────────────────────────────────────────────────────

@app.post("/upload-document")
async def upload_document(file: UploadFile = File(...)):
    tmp_path = None
    try:
        from services.blob_service import upload_document as blob_upload
        from services.rag_service import create_vector_db
        suffix = ("." + file.filename.rsplit(".", 1)[-1]) if "." in file.filename else ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        blob_upload(file_path=tmp_path, blob_name=file.filename)
        rebuild_result = create_vector_db()
        return {"status": "success", "blob_name": file.filename, "vector_db": rebuild_result}
    except Exception as exc:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(exc)})
    finally:
        if tmp_path: os.unlink(tmp_path)

@app.delete("/delete-document/{blob_name}")
def delete_blob_document(blob_name: str):
    try:
        from services.blob_service import delete_document
        delete_document(blob_name)
        return {"status": "success", "message": "Deleted successfully"}
    except Exception as exc:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(exc)})


# ─────────────────────────────────────────────────────────────
# Analytics (Power BI)
# ─────────────────────────────────────────────────────────────

@app.get("/analytics/agent-insights")
def analytics_agent_insights():
    try:
        from services.analytics_service import get_agent_insights
        return get_agent_insights()
    except Exception as exc:
        logger.error(f"Agent insights error: {exc}", exc_info=True)
        return JSONResponse(status_code=500, content={"status": "error", "message": str(exc)})


# ─────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────
# Inventory Analytics
# ─────────────────────────────────────────────────────────────

@app.get("/analytics/inventory")
def analytics_inventory():
    return {
        "kpis": {
            "total_stores": 45,
            "critical_stock_stores": 5,
            "warning_stock_stores": 12,
            "stable_stock_stores": 28
        },

        "anomaly_summary": {
            "anomaly_rate_pct": 8.5
        },

        "store_inventory_status": [
            {
                "store_id": 1,
                "avg_weekly_sales": 25000,
                "sales_volatility": 4200,
                "stock_status": "Stable"
            },
            {
                "store_id": 2,
                "avg_weekly_sales": 18000,
                "sales_volatility": 5100,
                "stock_status": "Warning"
            },
            {
                "store_id": 3,
                "avg_weekly_sales": 12000,
                "sales_volatility": 8200,
                "stock_status": "Critical"
            },
            {
                "store_id": 4,
                "avg_weekly_sales": 30000,
                "sales_volatility": 2500,
                "stock_status": "Healthy"
            },
            {
                "store_id": 5,
                "avg_weekly_sales": 22000,
                "sales_volatility": 3700,
                "stock_status": "Stable"
            }
        ]
    }
    
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)