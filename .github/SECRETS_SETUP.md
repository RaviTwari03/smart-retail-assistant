# GitHub Secrets Setup

Go to: **GitHub → RaviTwari03/smart-retail-assistant → Settings → Secrets and variables → Actions → New repository secret**

Add these 2 secrets:

---

## 1. DOCKER_HUB_TOKEN

Your Docker Hub access token (not your password).

**How to get it:**
1. Go to https://hub.docker.com → Account Settings → Security
2. Click "New Access Token"
3. Name it `smart-retail-ci`
4. Copy the token and paste it as the secret value

---

## 2. AZURE_CREDENTIALS

A JSON object with your Azure service principal credentials.

**How to get it — run this in Azure Cloud Shell or your terminal:**

```bash
az ad sp create-for-rbac \
  --name "smart-retail-github-actions" \
  --role contributor \
  --scopes /subscriptions/<YOUR_SUBSCRIPTION_ID>/resourceGroups/smart-retail-rg \
  --sdk-auth
```

Replace `<YOUR_SUBSCRIPTION_ID>` with your Azure subscription ID
(find it in Azure Portal → Subscriptions).

The command outputs JSON like this — paste the **entire JSON** as the secret value:

```json
{
  "clientId": "...",
  "clientSecret": "...",
  "subscriptionId": "...",
  "tenantId": "...",
  "activeDirectoryEndpointUrl": "...",
  "resourceManagerEndpointUrl": "...",
  "activeDirectoryGraphResourceId": "...",
  "sqlManagementEndpointUrl": "...",
  "galleryEndpointUrl": "...",
  "managementEndpointUrl": "..."
}
```

---

## Pipeline Flow

```
Push to main
    ↓
🧪 Backend Tests (pytest)     🎨 Frontend Build Check
    ↓                              ↓
         Both pass?
              ↓
    🐳 Build & Push Docker Images
       - backend:latest + backend:<sha>
       - frontend:latest + frontend:<sha>
              ↓
    🚀 Deploy to Azure App Service
       - Pulls new backend image
       - Health check: GET /health → 200
```

## What triggers what

| Event | Tests | Build | Deploy |
|---|---|---|---|
| Push to `main` | ✅ | ✅ | ✅ |
| Pull Request | ✅ | ❌ | ❌ |
