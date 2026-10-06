# Deployment Guide

> **LeakedIn** — AI-powered fake job offer detector  
> This guide covers three free hosting options: **Render**, **Railway**, and **Hugging Face Spaces**.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Variables](#environment-variables)
3. [Option A — Render (Recommended)](#option-a--render-recommended)
4. [Option B — Railway](#option-b--railway)
5. [Option C — Hugging Face Spaces (Gradio)](#option-c--hugging-face-spaces-gradio)
6. [Docker (Self-hosted)](#docker-self-hosted)
7. [Post-Deployment Checklist](#post-deployment-checklist)

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.10+ | Required for match-case syntax in `aggregator.py` |
| Trained model | `backend/models/job_detector_model.joblib` must exist |
| `requirements.txt` | All packages listed; EasyOCR downloads models on first run |

Train the model locally before deploying:
```bash
python -m backend.scripts.train_pipeline
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `ALLOWED_ORIGINS` | `*` | Comma-separated CORS origins, e.g. `https://yourapp.com` |
| `RATE_LIMIT` | `30/minute` | Max requests per IP per minute |
| `LOG_LEVEL` | `INFO` | Uvicorn log level |

---

## Option A — Render (Recommended)

Render offers a **free tier** with 512 MB RAM — sufficient for inference without EasyOCR (EasyOCR requires ~1 GB; disable or use the document/text endpoints only on free tier).

### Steps

1. **Fork the repo** and push to GitHub.

2. **Create a new Web Service** on [render.com](https://render.com):
   - Connect your GitHub repo
   - **Runtime**: Python 3
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && python -m backend.scripts.train_pipeline
     ```
   - **Start Command**:
     ```bash
     uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Environment**: Add `ALLOWED_ORIGINS=https://your-frontend.onrender.com`

3. **Deploy frontend** as a separate Static Site:
   - Root directory: `frontend/`
   - Publish directory: `.`
   - No build command needed

4. Update `script.js` API base URL:
   ```js
   const API_BASE = "https://your-backend.onrender.com";
   ```

> [!NOTE]
> Render free tier sleeps after 15 minutes of inactivity. First request takes ~30s to cold-start.

---

## Option B — Railway

Railway offers \$5 free credit/month — enough for light workloads.

### Steps

1. Install Railway CLI:
   ```bash
   npm i -g @railway/cli
   railway login
   ```

2. From the project root:
   ```bash
   railway init
   railway up
   ```

3. Set environment variables in the Railway dashboard or:
   ```bash
   railway variables set ALLOWED_ORIGINS=https://your-frontend.up.railway.app
   ```

4. Railway auto-detects `Dockerfile` — the multi-stage build runs automatically.

5. For the frontend, create a second Railway service pointing to the `frontend/` directory with Nginx.

> [!TIP]
> Use a `railway.toml` to pin the Dockerfile path if Railway doesn't auto-detect it.

```toml
[build]
  dockerfile = "Dockerfile"

[deploy]
  startCommand = "uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT"
  healthcheckPath = "/health"
  healthcheckTimeout = 300
```

---

## Option C — Hugging Face Spaces (Gradio)

Best for demos. Free, public, and discoverable. Requires wrapping the API in a Gradio interface.

### Steps

1. Create a new **Space** at [huggingface.co/spaces](https://huggingface.co/spaces):
   - SDK: **Gradio**
   - Hardware: **CPU Free** (or CPU Basic for EasyOCR)

2. Create `app.py` at the project root:
   ```python
   import gradio as gr
   from backend.app.api.routes import _run_pipeline

   def analyze(text, company, email):
       result = _run_pipeline(text, company, email)
       return (
           f"**Risk Score**: {result['risk_score']}/100  \n"
           f"**Level**: {result['risk_level']}  \n"
           f"**Verdict**: {result['verdict']}  \n\n"
           f"**Red Flags**: {len(result['red_flags'])}"
       )

   demo = gr.Interface(
       fn=analyze,
       inputs=[
           gr.Textbox(label="Job Offer Text", lines=8),
           gr.Textbox(label="Company Name (optional)"),
           gr.Textbox(label="Contact Email (optional)"),
       ],
       outputs=gr.Markdown(label="Analysis"),
       title="LeakedIn — Fake Job Offer Detector",
       description="Paste a suspicious job offer to check for fraud indicators.",
   )

   if __name__ == "__main__":
       demo.launch()
   ```

3. Add `gradio` to `requirements.txt`.

4. Push to the Space repo:
   ```bash
   git remote add space https://huggingface.co/spaces/YOUR_USERNAME/leakedin
   git push space main
   ```

---

## Docker (Self-hosted)

For VPS, home server, or local production-grade deployment:

```bash
# Clone and build
git clone https://github.com/your-org/leakedin.git
cd leakedin

# Train model first
pip install -r requirements.txt
python -m backend.scripts.train_pipeline

# Launch everything
docker compose up --build -d

# Check logs
docker compose logs -f backend

# Stop
docker compose down
```

Services:
- **Frontend**: http://localhost:5500
- **API Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

---

## Post-Deployment Checklist

- [ ] `/health` returns `{"status": "ok"}`
- [ ] `/api/analyze/text` returns a valid JSON response
- [ ] CORS is correctly configured for your frontend domain
- [ ] Rate limiting is active (test with rapid requests)
- [ ] `ALLOWED_ORIGINS` does **not** include `*` in production
- [ ] `backend/app/db/reputation.db` is backed by a persistent volume
- [ ] EasyOCR models downloaded successfully (check logs for `Using GPU: False`)
