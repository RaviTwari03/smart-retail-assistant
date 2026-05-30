import logging
import os
import tempfile

import uvicorn
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# =========================
# LOGGING SETUP
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__)

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
# Blob Storage - List Documents
# =========================

@app.get("/blob-documents")
def list_blob_documents():
    """
    List all documents stored in Azure Blob Storage knowledge base container.

    Returns:
        200: {"status": "success", "documents": [...]}
        500: {"status": "error", "message": "..."}
    """
    try:
        from services.blob_service import list_documents

        docs = list_documents()

        return {
            "status": "success",
            "documents": docs
        }

    except Exception as e:
        logger.error(f"Failed to list blob documents: {str(e)}", exc_info=True)

        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e)
            }
        )


# =========================
# Blob Storage - Upload Document
# =========================

@app.post("/upload-document")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document to Azure Blob Storage knowledge base container.

    Args:
        file: Multipart file upload (PDF or TXT)

    Returns:
        200: {"status": "success", "blob_name": "..."}
        400: {"status": "error", "message": "..."}
        500: {"status": "error", "message": "..."}
    """
    if not file or not file.filename:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": "No file provided. Please attach a file to the request."
            }
        )

    try:
        from services.blob_service import upload_document as blob_upload

        # Save upload to a temp file, then push to blob storage
        suffix = "." + file.filename.rsplit(".", 1)[-1] if "." in file.filename else ""

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        try:
            result = blob_upload(file_path=tmp_path, blob_name=file.filename)
        finally:
            # Always remove the temp file
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

        return {
            "status": "success",
            "blob_name": result["blob_name"]
        }

    except Exception as e:
        logger.error(f"Failed to upload document '{file.filename}': {str(e)}", exc_info=True)

        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e)
            }
        )


# =========================
# Blob Storage - Delete Document
# =========================

@app.delete("/delete-document/{blob_name}")
def delete_blob_document(blob_name: str):
    """
    Delete a document from Azure Blob Storage knowledge base container.

    Args:
        blob_name: Name of the blob to delete (path parameter)

    Returns:
        200: {"status": "success", "message": "..."}
        404: {"status": "error", "message": "..."}
        500: {"status": "error", "message": "..."}
    """
    try:
        from services.blob_service import delete_document, BlobNotFoundError

        delete_document(blob_name)

        return {
            "status": "success",
            "message": f"Blob '{blob_name}' deleted successfully"
        }

    except Exception as e:
        from services.blob_service import BlobNotFoundError

        if isinstance(e, BlobNotFoundError):
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": str(e)
                }
            )

        logger.error(f"Failed to delete blob '{blob_name}': {str(e)}", exc_info=True)

        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e)
            }
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