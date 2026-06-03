# Hosting & Deployment Guide

This guide describes how to host the **Quantum-Assisted ML Framework for Drug Repurposing** in production.

---

## 🚀 Deployment Options

Choose the hosting strategy that best fits your needs:

| Option | Ideal For | Services | Cost | Difficulty |
| :--- | :--- | :--- | :--- | :--- |
| **Option A: Cloud PaaS (Recommended)** | Free-tier demos, rapid deployment, automated updates. | **Backend:** Render<br>**Frontend:** Vercel<br>**Database:** MongoDB Atlas | **Free** (utilizing free tiers) | Easy |
| **Option B: Containerized Self-Hosting** | Dedicated servers, custom cloud instances (VPS), local networks. | Dockerized containers orchestrating Nginx, Flask, Redis, MongoDB. | Cost of server | Medium |

---

## Option A: Cloud PaaS (Render + Vercel + MongoDB Atlas)

This configuration hosts each component on optimized cloud platforms.

### Step 1: Set Up MongoDB Atlas (Database)
1. Register for a free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).
2. Create a new shared cluster (e.g., M0 free tier).
3. In **Database Access**, create a user (keep the username and password handy).
4. In **Network Access**, add IP Address `0.0.0.0/0` to allow connections from Render.
5. In **Clusters** > **Connect**, choose **Drivers** and copy the Connection String. It will look like this:
   `mongodb+srv://<username>:<password>@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority`

### Step 2: Deploy Backend to Render
1. Register at [Render](https://render.com) and link your GitHub repository.
2. In Render, select **New** > **Web Service**.
3. Choose your repository and select the **Render Blueprint** (`render.yaml` automatically configures the details), or configure it manually:
   - **Name:** `qaml-backend`
   - **Language/Runtime:** `Python`
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python run.py`
4. Under **Advanced** > **Environment Variables**, configure the following:
   - `FLASK_ENV`: `production`
   - `SECRET_KEY`: *[Generate a strong 32-character hex key]* (Run `python -c "import secrets; print(secrets.token_hex(32))"`)
   - `JWT_SECRET_KEY`: *[Generate another strong 32-character hex key]*
   - `MONGO_URI`: *[Your MongoDB Atlas connection string from Step 1]*
   - `MONGODB_DB`: `quantum_drug_repurposing`
   - `CORS_ORIGINS`: `https://your-vercel-app-name.vercel.app` (You will update this once the Vercel frontend is deployed)
5. Click **Create Web Service**. Your backend will deploy. Note your backend URL (e.g., `https://qaml-backend.onrender.com`).

### Step 3: Deploy Frontend to Vercel
1. Register at [Vercel](https://vercel.com) and link your GitHub repository.
2. Click **Add New** > **Project** and import your repository.
3. In the project configure settings:
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend`
4. Under **Environment Variables**, add:
   - `VITE_API_BASE_URL`: *[Your Render backend URL, e.g. `https://qaml-backend.onrender.com`]* (Origin only—do **not** append `/api/v1` or a trailing slash).
5. Click **Deploy**. Vercel will compile the React app and host the static files. It will handle the SPA routing automatically using the provided `vercel.json` rewrite file.
6. **Important Final Step:** Copy your Vercel deployment URL (e.g. `https://your-vercel-app-name.vercel.app`), go back to your **Render Dashboard** for the backend service, update the `CORS_ORIGINS` environment variable to match this URL, and trigger a redeploy of the backend.

---

## Option B: Containerized Self-Hosting (Docker Compose)

This runs the entire stack inside containers on a single host machine (e.g., Ubuntu VPS or local server).

### Prerequisites
- Install **Docker** and **Docker Compose** on the host. ([Docker Installation Guide](https://docs.docker.com/engine/install/))

### Step 1: Clone and Configure
1. Clone the repository on the target server.
2. Copy the production environment file:
   ```bash
   cp .env.production .env
   ```
3. Edit the newly created `.env` file and generate secure random secrets:
   ```bash
   nano .env
   ```
   Generate the values using: `python -c "import secrets; print(secrets.token_hex(32))"`
   Update the `CORS_ORIGINS` value to match the public IP or domain of your server.

### Step 2: Spin Up the Stack
Run the following command from the repository root:
```bash
docker compose -f infra/docker-compose.prod.yml up -d --build
```

This starts:
- **MongoDB** on port `27017` (with health checks).
- **Redis** on port `6379`.
- **Flask API Backend** on port `5000`.
- **Celery Worker** (runs pipeline jobs asynchronously in the background).
- **Nginx Frontend Server** on port `80`.

### Step 3: Verify Running Services
List active containers and verify all have a status of `Up` (or `Up (healthy)`):
```bash
docker compose -f infra/docker-compose.prod.yml ps
```

To view backend service logs:
```bash
docker compose -f infra/docker-compose.prod.yml logs -f backend
```

To stop the services:
```bash
docker compose -f infra/docker-compose.prod.yml down
```

---

## 🛠️ Post-Deployment Verification

Verify that the services are communicating correctly. Replace `localhost` or `http://localhost:5000` with your deployed hostnames where applicable:

1. **Verify Backend Liveness:**
   Send a GET request to the health check endpoint:
   ```bash
   curl -I http://localhost:5000/api/v1/health
   ```
   **Expected Response:** `HTTP/1.1 200 OK` with JSON body `{"status":"ok", "service":"quantum-drug-repurposing"}`.

2. **Verify Frontend Static Assets:**
   Visit the frontend URL in your browser. The login screen should display immediately.

3. **Verify CORS and End-to-End Auth:**
   1. Register a new account on the frontend.
   2. Log in. If successful, you will be redirected to the Dashboard.
   3. Check the browser Console network tab (F12) to ensure requests are going to `/api/v1/stats` or `https://backend-url/api/v1/stats` and returning status code `200`.
