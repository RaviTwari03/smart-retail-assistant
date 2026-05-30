# GitHub Secrets Setup

Go to: **GitHub → RaviTwari03/smart-retail-assistant → Settings → Secrets and variables → Actions → New repository secret**

Add these **2 secrets** only:

---

## 1. DOCKER_HUB_TOKEN

Your Docker Hub access token.

**How to get it:**
1. Go to https://hub.docker.com → Account Settings → Security
2. Click **New Access Token** → name it `smart-retail-ci`
3. Copy the token and paste it as the secret value

---

## 2. AZURE_WEBAPP_PUBLISH_PROFILE

The publish profile XML from your Azure App Service.

**How to get it — run this command:**
```bash
az webapp deployment list-publishing-profiles \
  --name smart-assistant-api \
  --resource-group smart-retail-rg \
  --xml
```

Copy the **entire XML output** (starts with `<publishData>`) and paste it as the secret value.

> ✅ This approach works with Azure for Students subscriptions.
> No service principal or special permissions needed.

---

## Pipeline Flow

```
Push to main
    ↓
🧪 Backend Tests (pytest 67 tests)    🎨 Frontend Build Check
         ↓                                      ↓
              Both must pass
                    ↓
         🐳 Build & Push Docker Images
            backend:latest + backend:<sha>
            frontend:latest + frontend:<sha>
                    ↓
         🚀 Deploy to Azure App Service
            Pulls new backend image
            Health check → GET /health → 200 ✅
```

## Trigger summary

| Event | Tests | Build | Deploy |
|---|---|---|---|
| Push to `main` | ✅ | ✅ | ✅ |
| Pull Request | ✅ | ❌ | ❌ |
