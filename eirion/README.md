# EIRION — AI-Powered Precision Longevity Platform

> DNA + Lifestyle + Medications → Personalized Organ Health Forecasts

**ETGen AI Hackathon 2026 | Phase 0 Prototype**

---

## Quick Start (Local Dev)

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev  # → http://localhost:5173
```

### Docker (Full Stack)
```bash
cp .env.example .env       # fill in GEMINI_API_KEY if available
docker compose up --build
```

---

## Demo

Click **"Load Priya Example"** on the landing page for the canonical demo flow.

- Priya, 35F, CYP2D6 poor metabolizer, Ashwagandha + Metformin stack
- EIRION detects silent liver stress before labs show anything
- Predicts 15% liver efficiency drop by age 40
- Recommends 3 changes → liver maintained at 98% through age 50

---

## Project Structure

```
eirion/
├── backend/           # FastAPI (Python 3.11)
│   ├── engine/        # Scoring algorithm, knowledge tables, explainer
│   ├── models/        # Pydantic request/response schemas
│   ├── routers/       # FastAPI route handlers
│   ├── tests/         # pytest unit tests
│   └── data/          # mock_response.json fallback
├── frontend/          # React 18 + TypeScript + Vite
│   └── src/
│       ├── pages/     # Landing, Onboarding, Dashboard
│       ├── components/# UI components
│       ├── store/     # Zustand state
│       ├── api/       # React Query hooks
│       └── data/      # Priya prefill, mock response
└── docker-compose.yml
```

---

## Tech Stack (Phase 0)

| Layer | Tech |
|-------|------|
| Frontend | React 18 + TypeScript + Vite |
| UI | shadcn/ui + Tailwind CSS |
| Charts | Recharts |
| State | Zustand + React Query |
| Backend | FastAPI (Python 3.11) + Pydantic v2 |
| Engine | Deterministic rules-based (Phase 0) |
| Storage | In-memory / SQLite |
| GenAI | Gemini API (Google) for rec text |
| Testing | pytest | Railway.app / Render.com |

---

*EIRION — "Predict before it's too late. Personalize to your biology."*
*Confidential — Team EIRION | ETGen AI Hackathon 2026*
