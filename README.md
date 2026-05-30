# Smart Retail Assistant

**Left Shift Program 2026 – Data & AI (T5)**  
End-to-end Multi-Agent AI Platform with GenAI, Analytics & Azure Deployment.

---

## Architecture

```
React Frontend
    ↓
Azure App Service (Docker Container)
    ↓
FastAPI Backend
    ↓
Multi-Agent Orchestrator
    ├── Customer Support Agent  →  RAG + GPT-3.5-turbo
    ├── Inventory Agent         →  Stock classification
    ├── Forecast Agent          →  Prophet 7-day prediction
    ├── Data Analyst Agent      →  Walmart dataset insights
    └── Document Search Agent   →  Raw RAG chunk retrieval
         ↓
    RAG Pipeline
        Azure Blob Storage (knowledge-base)
            ↓ Download PDFs
            ↓ PyPDFLoader / TextLoader
            ↓ RecursiveCharacterTextSplitter (chunk=300, overlap=50)
            ↓ HuggingFaceEmbeddings (all-MiniLM-L6-v2)
            ↓ ChromaDB Vector Store
            ↓ Similarity Search (k=3)
         ↓
    Data Stores
        ├── Azure PostgreSQL  →  ChatHistory, ForecastRecords
        └── ChromaDB          →  Vector embeddings (./vector_db)
         ↓
    ML Models
        ├── Prophet            →  forecast_model.pkl
        ├── IsolationForest    →  anomaly_model.pkl
        └── OpenAI GPT-3.5    →  LLM synthesis
```

See [`assets/architecture_diagram.svg`](assets/architecture_diagram.svg) for the visual diagram.

---

## Azure Services Used

| Service | Purpose | Config |
|---|---|---|
| **Azure App Service** | Hosts the FastAPI backend as a Docker container | `smart-assistant-api` · Southeast Asia |
| **Azure Blob Storage** | Source of truth for RAG knowledge base PDFs | Container: `knowledge-base` |
| **Azure PostgreSQL** | Persistent storage for chat history and forecasts | Via `DATABASE_URL` |
| **Azure Bot Service** | Bot Framework endpoint (`/api/messages`) | `MICROSOFT_APP_ID` + `APP_PASSWORD` |

---

## Environment Variables

Set these in **Azure App Service → Settings → Environment Variables**:

| Variable | Required | Description |
|---|---|---|
| `AZURE_STORAGE_CONNECTION_STRING` | ✅ | Azure Storage account connection string |
| `AZURE_BLOB_CONTAINER` | ✅ | Blob container name (default: `knowledge-base`) |
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `OPENAI_API_KEY` | ✅ | OpenAI API key for LLM synthesis |
| `MICROSOFT_APP_ID` | Optional | Azure Bot Service app ID |
| `APP_PASSWORD` | Optional | Azure Bot Service app password |
| `PORT` | Optional | Server port (default: `8000`) |

For local development, copy `.env.example` to `.env` and fill in values.

---

## API Endpoints

### Core

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check / root |
| `GET` | `/health` | Service health status |
| `GET` | `/dashboard-metrics` | Revenue, alerts, trend summary |

### Machine Learning

| Method | Endpoint | Description | Body |
|---|---|---|---|
| `GET` | `/forecast` | 7-day Prophet sales forecast | — |
| `POST` | `/detect-anomaly` | IsolationForest anomaly detection | `{"sales": [float]}` |

### RAG / Knowledge Base

| Method | Endpoint | Description | Body |
|---|---|---|---|
| `POST` | `/search-documents` | Semantic search over knowledge base | `{"query": "string"}` |
| `GET` | `/blob-documents` | List all PDFs in Azure Blob Storage | — |
| `POST` | `/upload-document` | Upload PDF to Azure Blob Storage | `multipart/form-data` |
| `DELETE` | `/delete-document/{blob_name}` | Delete blob from Azure Blob Storage | — |

### Agents

| Method | Endpoint | Description | Body |
|---|---|---|---|
| `POST` | `/customer-support` | RAG + LLM customer support answer | `{"query": "string"}` |
| `POST` | `/retail-assistant` | Full multi-agent orchestrator | `{"query": "string", "stock": int}` |
| `GET` | `/chat-history` | Retrieve all saved chat interactions | — |

### Bot

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/messages` | Azure Bot Framework webhook |

---

## Multi-Agent System

### Agents

**Customer Support Agent** (`agents/customer_support/support_agent.py`)  
- Searches ChromaDB for relevant knowledge base chunks  
- Builds a grounded prompt with retrieved context  
- Calls GPT-3.5-turbo to synthesize a natural language answer  
- Falls back to raw chunk if OpenAI is unavailable  

**Inventory Agent** (`agents/inventory_agent/inventory_agent.py`)  
- Classifies stock level: Critical / Warning / Stable  

**Forecast Agent** (`agents/forecast_agent/forecast_agent.py`)  
- Runs Prophet model for 7-day sales prediction  
- Returns trend direction, peak day, and narrative summary  

**Data Analyst Agent** (`agents/data_analyst/data_analyst_agent.py`)  
- Analyzes Walmart dataset for store-level insights  
- Returns top stores, total revenue, holiday lift, trend  

**Document Search Agent** (`agents/document_search/document_search_agent.py`)  
- Returns raw RAG chunks for a query  
- Used by other agents and direct API consumers  

**Orchestrator** (`agents/orchestrator.py`)  
- Runs all 5 agents and returns a unified response  

---

## RAG Workflow

```
1. PDFs uploaded to Azure Blob Storage (knowledge-base container)
2. create_vector_db.py triggered:
   a. list_documents()  →  get all blob names
   b. download_document()  →  temp directory
   c. PyPDFLoader / TextLoader  →  extract text
   d. RecursiveCharacterTextSplitter  →  chunks (300 chars, 50 overlap)
   e. HuggingFaceEmbeddings (all-MiniLM-L6-v2)  →  vectors
   f. Chroma.from_documents()  →  persist to ./vector_db
   g. shutil.rmtree(temp_dir)  →  cleanup
3. search_documents(query):
   a. Load ChromaDB from ./vector_db
   b. similarity_search(query, k=3)
   c. Return page_content of top-3 chunks
4. Customer Support Agent:
   a. Calls search_documents()
   b. Builds RAG prompt with context
   c. Calls GPT-3.5-turbo
   d. Returns synthesized answer
```

**Knowledge Base Documents (in Azure Blob):**
- `customer_support_faq.pdf`
- `discount_policy.pdf`
- `inventory_rules.pdf`
- `store_policy.pdf`

---

## ML Models

### Prophet Forecasting (`services/forecast_service.py`)

- **Dataset**: Walmart weekly sales (45 stores, 2.5 years)
- **Model**: Facebook Prophet with yearly + weekly seasonality
- **Output**: 7-day forecast with `yhat`, `yhat_lower`, `yhat_upper`
- **Persistence**: `models/forecast_model.pkl`
- **Fallback**: Trains on-the-fly if no saved model exists

### Anomaly Detection (`services/anomaly_service.py`)

- **Model**: IsolationForest (scikit-learn)
- **Input**: List of weekly sales values
- **Output**: `[{"sales": float, "is_anomaly": bool}]`
- **Persistence**: `models/anomaly_model.pkl`

---

## Project Structure

```
smart-retail-assistant/
├── backend/
│   ├── agents/
│   │   ├── customer_support/support_agent.py   # RAG + LLM
│   │   ├── inventory_agent/inventory_agent.py  # Stock classification
│   │   ├── forecast_agent/forecast_agent.py    # Prophet insights
│   │   ├── data_analyst/data_analyst_agent.py  # Dataset analytics
│   │   ├── document_search/document_search_agent.py  # RAG retrieval
│   │   └── orchestrator.py                     # Multi-agent coordinator
│   ├── models/
│   │   ├── forecast_model.py / .pkl            # Prophet
│   │   └── anomaly_model.py / .pkl             # IsolationForest
│   ├── services/
│   │   ├── blob_service.py                     # Azure Blob Storage
│   │   ├── rag_service.py                      # RAG pipeline
│   │   ├── forecast_service.py                 # Prophet forecasting
│   │   ├── anomaly_service.py                  # Anomaly detection
│   │   └── db_service.py                       # PostgreSQL operations
│   ├── tests/
│   │   ├── test_forecast.py
│   │   ├── test_rag.py
│   │   └── test_api.py
│   ├── knowledge_base/                         # Local PDF backup
│   ├── vector_db/                              # ChromaDB persistence
│   ├── main.py                                 # FastAPI app
│   ├── database.py                             # SQLAlchemy setup
│   ├── db_models.py                            # ORM models
│   ├── create_vector_db.py                     # Vector DB builder
│   ├── train_model.py                          # Model training script
│   ├── requirements.txt
│   ├── Dockerfile
│   └── startup.sh
├── frontend/                                   # React app
├── data/Raw/Walmart.csv                        # Training dataset
├── assets/architecture_diagram.svg            # Architecture diagram
├── docker-compose.yml
└── .env.example
```

---

## Local Development

```bash
# 1. Clone and set up environment
cp .env.example .env
# Fill in AZURE_STORAGE_CONNECTION_STRING, DATABASE_URL, OPENAI_API_KEY

# 2. Start with Docker Compose
docker-compose up --build

# 3. Build vector database from Azure Blob Storage
docker exec -it <backend_container> python create_vector_db.py

# 4. Train ML models
docker exec -it <backend_container> python train_model.py

# 5. Run tests
cd backend
pip install pytest
pytest tests/ -v
```

---

## Deployment

The backend is deployed as a Docker container on **Azure App Service**:

- **Container image**: `index.docker.io/bytesaint03/smart-retail-assistant-backend:latest`
- **Runtime**: Linux · Python 3.11
- **Region**: Southeast Asia
- **URL**: `smart-assistant-api-abefc8fwbearcncb.southeastasia-01.azurewebsites.net`

To redeploy after changes:
```bash
docker build -t bytesaint03/smart-retail-assistant-backend:latest ./backend
docker push bytesaint03/smart-retail-assistant-backend:latest
# Azure App Service pulls the new image automatically on restart
```

---

## Testing

```bash
cd backend
pytest tests/ -v

# Individual test files
pytest tests/test_forecast.py -v
pytest tests/test_rag.py -v
pytest tests/test_api.py -v
```

---

## Power BI Dashboard

Connect Power BI to the FastAPI endpoints:

| Visual | Data Source | Endpoint |
|---|---|---|
| Revenue Card | Dashboard metrics | `GET /dashboard-metrics` |
| Forecast Trend Line | Prophet predictions | `GET /forecast` |
| Inventory Alert Gauge | Stock status | `POST /retail-assistant` |
| Anomaly Scatter | Anomaly detection | `POST /detect-anomaly` |
| Chat History Table | PostgreSQL | `GET /chat-history` |

Use **Power BI → Get Data → Web** and point to your Azure App Service URL.
