# 🛒 Smart Retail Assistant

An AI-powered multi-agent retail analytics platform built using:

- FastAPI
- ReactJS
- Machine Learning
- RAG (Retrieval-Augmented Generation)
- Azure Bot Service
- Docker
- PostgreSQL
- Power BI
- CI/CD with GitHub Actions

---

# 📌 Project Overview

This project was developed as part of the:

**Left Shift Program 2026 – Data & AI Capstone Project** :contentReference[oaicite:0]{index=0}

The platform provides:

- Retail demand forecasting
- AI-powered customer support
- Inventory anomaly detection
- Power BI analytics dashboard
- Azure chatbot integration
- Multi-agent orchestration system

---

# 🧠 Features

## 📈 Forecast Analytics
- Sales prediction using ML forecasting
- Future revenue estimation
- Trend analysis

## 🤖 AI Assistant
- Customer support chatbot
- Retail policy Q&A
- RAG-based document retrieval

## 🚨 Inventory Monitoring
- Low stock alerts
- Inventory anomaly detection
- Smart retail insights

## 📊 Power BI Dashboard
- Revenue metrics
- Inventory analytics
- Sales trends
- Business KPIs

---

# 🏗️ Tech Stack

## Frontend
- ReactJS
- Axios
- CSS

## Backend
- FastAPI
- Python
- SQLAlchemy

## AI / ML
- Prophet Forecasting
- RAG Pipeline
- Vector Database
- Multi-Agent Architecture

## Database
- PostgreSQL

## Cloud & DevOps
- Docker
- Docker Compose
- Azure Bot Service
- ngrok
- GitHub Actions

---

# 📂 Project Structure

```bash
smart-retail-assistant/
│
├── backend/
├── frontend/
├── data/
├── assets/
├── docker-compose.yml
└── README.md
```

---

# 🖥️ Frontend Screenshots

## Dashboard

![Dashboard](assets/dashboard.png)

---

## Forecast Analytics

![Forecast](assets/forecast.png)

---

## AI Assistant

![Assistant](assets/assistant.png)

---

## Inventory Monitoring

![Inventory](assets/inventory.png)

---

# 📊 Power BI Dashboard

## Dashboard Page 1

![PowerBI 1](assets/powerbi_1.png)

---

## Dashboard Page 2

![PowerBI 2](assets/powerbi_2.png)

---

## Dashboard Page 3

![PowerBI 3](assets/powerbi_3.png)

---

# ☁️ Azure Bot Service

Azure AI chatbot integration using Azure Bot Framework.

![Azure Bot](assets/azure_bot.png)

---

# 🐳 Docker Setup

## Build Containers

```bash
docker-compose build --no-cache
```

## Run Containers

```bash
docker-compose up
```

## Stop Containers

```bash
docker-compose down
```

---

# 🔥 Run Project Locally

## Backend

```bash
cd backend

python -m venv venv

source venv/bin/activate

pip install -r requirements.txt

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## Frontend

```bash
cd frontend

npm install

npm start
```

---

# 🌐 ngrok Setup for Azure Bot

## Install ngrok

```bash
brew install ngrok/ngrok/ngrok
```

---

## Authenticate ngrok

```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

---

## Expose FastAPI Backend

```bash
ngrok http 8000
```

Copy the HTTPS forwarding URL.

Example:

```bash
https://abc123.ngrok-free.app
```

---

# 🤖 Azure Bot Endpoint

Set messaging endpoint in Azure:

```bash
https://your-ngrok-url.ngrok-free.app/api/messages
```

---

# ⚙️ CI/CD Pipeline (GitHub Actions)

Create:

```bash
.github/workflows/deploy.yml
```

Add:

```yaml
name: Smart Retail Assistant CI/CD

on:
  push:
    branches:
      - main

jobs:

  build-and-test:

    runs-on: ubuntu-latest

    steps:

      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install Backend Dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Install Frontend Dependencies
        run: |
          cd frontend
          npm install

      - name: Build Docker Containers
        run: docker-compose build
```

---

# 🗄️ Database Setup

## PostgreSQL Connection

```python
DATABASE_URL = "postgresql://username:password@localhost:5432/retail_db"
```

---

# 🚀 APIs

| API | Description |
|---|---|
| `/dashboard-metrics` | Dashboard analytics |
| `/forecast` | Sales forecasting |
| `/customer-support` | AI assistant |
| `/chat-history` | Chat history |
| `/inventory-alerts` | Inventory monitoring |

---

# 📌 Deployment

The project supports:

- Local Deployment
- Docker Deployment
- Azure Deployment

---

# 📚 Capstone Requirements Covered

✅ Python Fullstack APIs  
✅ Machine Learning  
✅ Multi-Agent AI  
✅ RAG Pipeline  
✅ Azure Bot Integration  
✅ Docker Deployment  
✅ CI/CD Pipeline  
✅ Power BI Dashboard  
✅ PostgreSQL Database  

---

# 👨‍💻 Author

## Ravi Kumar Tiwari

B.Tech CSE  
Galgotias University

GitHub:
https://github.com/RaviTwari03

---

# ⭐ Future Improvements

- Real-time streaming analytics
- LLM fine-tuning
- Azure OpenAI integration
- Vector search optimization
- Role-based authentication
- Kubernetes deployment
