"""
Smart Retail Assistant — FastAPI Backend
=========================================
All existing APIs preserved.
New behaviour:
  - Startup: auto-build vector DB if it doesn't exist
  - Upload: rebuild vector DB after every successful upload
  - Search: safe error responses when DB is missing
"""

import logging
import os
import tempfile

import uvicorn
from fastapi import FastAPI, File, Request, UploadFile
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
    """
    On application startup:
      1. Log environment status (Azure vars present/missing)
      2. If vector_db does not exist → build it from Azure Blob Storage
      3. Never block startup — all failures are logged and swallowed
    """
    logger.info("=" * 60)
    logger.info("Smart Retail Assistant — startup")
    logger.info("=" * 60)

    # Log Azure config status (values masked)
    conn_str   = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
    container  = os.getenv("AZURE_BLOB_CONTAINER", "knowledge-base")
    logger.info(
        f"Azure Blob Storage: "
        f"connection_string={'SET' if conn_str else 'NOT SET'}, "
        f"container='{container}'"
    )

    # Auto-build vector DB if missing
    try:
        from services.rag_service import vector_db_exists, create_vector_db

        if vector_db_exists():
            logger.info("Vector database already exists — skipping auto-build")
        else:
            logger.info(
                "Vector database not found — building from Azure Blob Storage..."
            )
            result = create_vector_db()
            logger.info(f"Startup vector DB build result: {result}")

    except Exception as exc:
        # Never block startup
        logger.warning(
            f"Startup vector DB build failed (non-fatal): {exc}",
            exc_info=True,
        )

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
    """
    Semantic search over the knowledge base.

    Returns a meaningful error if the vector DB is not ready
    instead of crashing.
    """
    try:
        from services.rag_service import search_documents
        results = search_documents(data.query)
        return {"status": "success", "query": data.query, "results": results}

    except FileNotFoundError as exc:
        logger.warning(f"Search attempted but vector DB missing: {exc}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": (
                    "Knowledge base is not ready. "
                    "Upload documents and wait for the index to rebuild."
                ),
            },
        )
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
        result = [
            {"id": c.id, "query": c.query, "response": c.response}
            for c in chats
        ]
        db.close()
        return {"status": "success", "history": result}
    except Exception as exc:
        logger.error(f"Chat history error: {exc}", exc_info=True)
        return {"status": "error", "message": str(exc)}


# ─────────────────────────────────────────────────────────────
# Azure Bot
# ─────────────────────────────────────────────────────────────

@app.post("/api/messages")
async def bot_messages(request: Request):
    try:
        body = await request.json()
        user_message = body.get("text", "")
        return {"type": "message", "text": f"Hello Ravi 👋 You said: {user_message}"}
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(exc)},
        )


# ─────────────────────────────────────────────────────────────
# Blob Storage — List
# ─────────────────────────────────────────────────────────────

@app.get("/blob-documents")
def list_blob_documents():
    """List all documents in the Azure Blob Storage knowledge-base container."""
    try:
        from services.blob_service import list_documents
        docs = list_documents()
        logger.info(f"Listed {len(docs)} blob document(s)")
        return {"status": "success", "documents": docs}
    except Exception as exc:
        logger.error(f"list_blob_documents error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(exc)},
        )


# ─────────────────────────────────────────────────────────────
# Blob Storage — Upload  (auto-rebuilds vector DB)
# ─────────────────────────────────────────────────────────────

@app.post("/upload-document")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document to Azure Blob Storage, then automatically
    rebuild the ChromaDB vector database so the document is
    immediately searchable.

    Returns:
        200: {"status": "success", "blob_name": str, "vector_db": dict}
        400: {"status": "error", "message": str}   — missing file
        500: {"status": "error", "message": str}   — upload / rebuild failure
    """
    if not file or not file.filename:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": "No file provided. Attach a PDF or TXT file.",
            },
        )

    tmp_path: str | None = None

    try:
        from services.blob_service import upload_document as blob_upload
        from services.rag_service import create_vector_db

        # ── 1. Save to temp file ──────────────────────────────
        suffix = (
            "." + file.filename.rsplit(".", 1)[-1]
            if "." in file.filename
            else ""
        )
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # ── 2. Upload to Azure Blob Storage ───────────────────
        logger.info(f"Uploading '{file.filename}' to Azure Blob Storage")
        upload_result = blob_upload(file_path=tmp_path, blob_name=file.filename)
        logger.info(f"Upload complete: {upload_result}")

        # ── 3. Rebuild vector DB ──────────────────────────────
        logger.info(
            f"Rebuilding vector database after upload of '{file.filename}'"
        )
        rebuild_result = create_vector_db()
        logger.info(f"Vector DB rebuild result: {rebuild_result}")

        return {
            "status": "success",
            "blob_name": upload_result["blob_name"],
            "vector_db": rebuild_result,
        }

    except Exception as exc:
        logger.error(
            f"upload_document failed for '{file.filename}': {exc}",
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(exc)},
        )

    finally:
        # Always clean up the temp file
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────
# Blob Storage — Delete
# ─────────────────────────────────────────────────────────────

@app.delete("/delete-document/{blob_name}")
def delete_blob_document(blob_name: str):
    """
    Delete a document from Azure Blob Storage.

    Returns:
        200: {"status": "success", "message": str}
        404: {"status": "error", "message": str}   — blob not found
        500: {"status": "error", "message": str}   — unexpected error
    """
    try:
        from services.blob_service import delete_document, BlobNotFoundError
        delete_document(blob_name)
        logger.info(f"Deleted blob: '{blob_name}'")
        return {
            "status": "success",
            "message": f"Blob '{blob_name}' deleted successfully",
        }

    except Exception as exc:
        from services.blob_service import BlobNotFoundError

        if isinstance(exc, BlobNotFoundError):
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": str(exc)},
            )

        logger.error(f"delete_blob_document error for '{blob_name}': {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(exc)},
        )


# ─────────────────────────────────────────────────────────────
# Analytics (Power BI)
# ─────────────────────────────────────────────────────────────

@app.get("/analytics/revenue")
def analytics_revenue():
    try:
        from services.analytics_service import get_revenue_analytics
        return get_revenue_analytics()
    except Exception as exc:
        logger.error(f"Revenue analytics error: {exc}", exc_info=True)
        return JSONResponse(status_code=500, content={"status": "error", "message": str(exc)})


@app.get("/analytics/inventory")
def analytics_inventory():
    try:
        from services.analytics_service import get_inventory_analytics
        return get_inventory_analytics()
    except Exception as exc:
        logger.error(f"Inventory analytics error: {exc}", exc_info=True)
        return JSONResponse(status_code=500, content={"status": "error", "message": str(exc)})


@app.get("/analytics/forecast")
def analytics_forecast():
    try:
        from services.analytics_service import get_forecast_analytics
        return get_forecast_analytics()
    except Exception as exc:
        logger.error(f"Forecast analytics error: {exc}", exc_info=True)
        return JSONResponse(status_code=500, content={"status": "error", "message": str(exc)})


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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
