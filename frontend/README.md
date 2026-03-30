# EIRION Frontend — React 19 + TypeScript + Vite

<div align="center">

[![React](https://img.shields.io/badge/React-19.2-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-8.0-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vite.dev/)
[![Tailwind](https://img.shields.io/badge/Tailwind_CSS-4.2-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)

*The React SPA powering EIRION's precision longevity dashboard*

</div>

---

## Overview

The EIRION frontend is a **React 19 Single Page Application** built with TypeScript and Vite 8. It provides:

- 🧙 **9-step onboarding wizard** — collects patient demographics, genetics, labs, lifestyle, and regimen
- 📊 **14-widget analysis dashboard** — organ scores, trajectory charts, DDI flags, AI recommendations
- 🧬 **23andMe SNP parser** — client-side parsing of raw `.txt` genetic data files
- 📄 **Clinical PDF export** — download a 9-page clinical report from the backend
- 💬 **AI chat** — Gemini-powered conversational health assistant
- 🔐 **JWT authentication** — register, login, profile management

---

## Table of Contents

- [Architecture](#architecture)
- [Directory Structure](#directory-structure)
- [Getting Started](#getting-started)
- [Pages](#pages)
- [Components](#components)
- [State Management](#state-management)
- [Type System](#type-system)
- [API Integration](#api-integration)
- [Build & Deployment](#build--deployment)
- [Dependencies](#dependencies)

---

## Architecture

```
┌───────────────────────────────────────────────┐
│              React 19 SPA                      │
│                                                │
│  ┌────────────┐  ┌───────────────┐            │
│  │   Pages    │  │  Components   │            │
│  │  (7 pages) │  │ (30+ widgets) │            │
│  └─────┬──────┘  └───────┬───────┘            │
│        │                  │                    │
│        └────────┬─────────┘                    │
│                 │                              │
│  ┌──────────────┴──────────────┐               │
│  │       Zustand Stores        │               │
│  │  wizardStore │ authStore    │               │
│  │  notificationStore          │               │
│  └──────────────┬──────────────┘               │
│                 │                              │
│  ┌──────────────┴──────────────┐               │
│  │        API Layer            │               │
│  │   Axios / Fetch → Backend   │               │
│  └─────────────────────────────┘               │
└───────────────────────────────────────────────┘
         │
         │ HTTP / JWT
         ▼
   FastAPI Backend (:8000)
```

### State Flow

```
User Input → Wizard Store → API Call → Analysis Response → Dashboard Render
                                              │
                                      Stored in wizardStore.analysisResult
                                              │
                              ┌────────────────┼────────────────┐
                              │                │                │
                         OrganScorecard  TrajectoryChart  RecommendationFeed
                              │                │                │
                              └────────────────┴────────────────┘
```

---

## Directory Structure

```
frontend/
├── index.html                     # HTML entrypoint (title, meta tags)
├── package.json                   # Dependencies and scripts
├── vite.config.ts                 # Vite 8 configuration
│                                  #   - React + Tailwind CSS plugins
│                                  #   - @ path alias → ./src
│                                  #   - Manual chunk splitting (vendor, charts, icons, auth, utils)
├── tsconfig.json                  # TypeScript project config
├── tsconfig.app.json              # App-specific TS config
├── tsconfig.node.json             # Node/Vite TS config
├── eslint.config.js               # ESLint flat config
├── Dockerfile                     # Multi-stage build (Node → nginx)
│
└── src/
    ├── main.tsx                   # React DOM render entry point
    ├── App.tsx                    # Root component
    │                              #   - BrowserRouter with 7 routes
    │                              #   - SmartHome: auto-redirect authenticated users to /dashboard
    │                              #   - ProtectedRoute: JWT-gated route wrapper
    │                              #   - AppHeader: navigation bar with auth state, notification bell
    │                              #   - Auto-logout on JWT expiry (5-min check interval)
    │
    ├── App.css                    # Global app styles (3K)
    ├── index.css                  # Base CSS reset and tokens
    ├── types.ts                   # Full TypeScript type definitions (249 lines, 8K)
    │                              #   Mirrors all backend Pydantic models exactly
    │
    ├── pages/                     # ═══ PAGE COMPONENTS ═══
    │   ├── Landing.tsx            # Auth-aware landing page (6K)
    │   │                          #   - Hero section with value proposition
    │   │                          #   - "Start Your Analysis" CTA → /onboarding
    │   │                          #   - "Try Priya Demo" button → /demo
    │   │                          #   - Auth-aware: shows login/register or dashboard link
    │   │
    │   ├── Login.tsx              # Login form (4.6K)
    │   │                          #   - Email + password → authStore.login()
    │   │                          #   - Error display, loading state
    │   │                          #   - Links to /register
    │   │
    │   ├── Register.tsx           # Registration form (6K)
    │   │                          #   - Email + full name + password + confirm
    │   │                          #   - authStore.register() → auto-login
    │   │                          #   - Links to /login
    │   │
    │   ├── Wizard.tsx             # 9-step onboarding orchestrator (5.3K)
    │   │                          #   - Step progress bar with step labels
    │   │                          #   - Renders current step component
    │   │                          #   - Back/Next/Submit navigation
    │   │                          #   - Submits AnalysisRequest to POST /analysis/run
    │   │                          #   - Redirects to /dashboard on success
    │   │
    │   ├── Dashboard.tsx          # Full analysis dashboard (9K)
    │   │                          #   - Reads analysisResult from wizardStore
    │   │                          #   - Renders 14 dashboard widgets in a responsive grid
    │   │                          #   - "Re-run Analysis" and "New Analysis" actions
    │   │                          #   - Conditional rendering based on available data
    │   │
    │   ├── Demo.tsx               # Priya demo scenario (26K — largest page)
    │   │                          #   - Pre-filled canonical test case
    │   │                          #   - Priya, 35F, CYP2D6 poor metabolizer
    │   │                          #   - Ashwagandha + Atorvastatin + SLCO1B1 reduced function
    │   │                          #   - Full mock analysis result with all organ scores
    │   │                          #   - Renders complete dashboard without API call
    │   │
    │   └── ProfileSettings.tsx    # User profile & settings (15K)
    │                              #   - View/edit name
    │                              #   - Change password (current + new + confirm)
    │                              #   - Notification preferences
    │                              #   - Data export (download analysis as JSON)
    │                              #   - Reset analysis / clear data
    │                              #   - Account info (email, member since)
    │
    ├── components/
    │   ├── wizard/                # ═══ 13 WIZARD STEP COMPONENTS ═══
    │   │   │
    │   │   ├── Step1Demographics.tsx    # Age, sex, weight, height, ethnicity (4K)
    │   │   │                            #   - Validated number inputs with min/max
    │   │   │                            #   - Sex selector (male/female/other)
    │   │   │
    │   │   ├── Step2Conditions.tsx      # Pre-existing conditions (7.6K)
    │   │   │                            #   - Searchable condition list (22 conditions)
    │   │   │                            #   - Severity selector per condition
    │   │   │                            #   - Diagnosed vs self-reported toggle
    │   │   │
    │   │   ├── Step2Genetics.tsx        # Basic genetic entry (5.9K)
    │   │   │
    │   │   ├── Step3GeneticUpload.tsx   # 23andMe SNP file upload (8.6K)
    │   │   │                            #   - Drag-and-drop .txt file upload
    │   │   │                            #   - Client-side parsing: rsIDs → snp_pgx_map.json
    │   │   │                            #   - Infers CYP metabolizer phenotypes automatically
    │   │   │                            #   - Shows parsed diplotypes + metabolizer results
    │   │   │
    │   │   ├── Step3Lifestyle.tsx       # Basic lifestyle (4.4K)
    │   │   ├── Step3Diet.tsx            # Diet type and macros (8.1K)
    │   │   │
    │   │   ├── Step4GeneticManual.tsx   # Manual CYP metabolizer entry (5.9K)
    │   │   │                            #   - 7 CYP enzyme dropdowns
    │   │   │                            #   - MTHFR variant selectors
    │   │   │                            #   - SLCO1B1 function selector
    │   │   │
    │   │   ├── Step4Regimen.tsx         # Basic regimen entry (6.7K)
    │   │   │
    │   │   ├── Step5LabUpload.tsx       # Lab report image upload (9K)
    │   │   │                            #   - Drag-and-drop image upload
    │   │   │                            #   - Sends to POST /extraction/parse-labs
    │   │   │                            #   - Gemini Vision OCR → structured lab values
    │   │   │                            #   - User can review + edit extracted values
    │   │   │
    │   │   ├── Step5Labs.tsx            # Manual lab entry (7K)
    │   │   │                            #   - LFT: ALT, AST, GGT, ALP, Albumin, Bilirubin
    │   │   │                            #   - KFT: Creatinine, eGFR, BUN, Uric Acid
    │   │   │                            #   - Metabolic: HbA1c, Fasting Glucose
    │   │   │                            #   - Cardiac: LDL, HDL, Triglycerides, hsCRP
    │   │   │
    │   │   ├── Step6Lifestyle.tsx       # Deep lifestyle intake (15K — largest wizard step)
    │   │   │                            #   - Sleep hours + quality sliders
    │   │   │                            #   - Stress level + cognitive load
    │   │   │                            #   - Exercise, resistance training
    │   │   │                            #   - Alcohol, smoking status
    │   │   │                            #   - Environmental toxin exposure
    │   │   │                            #   - Sunlight, screen time, hydration
    │   │   │
    │   │   ├── Step6Confirm.tsx         # Review & confirm (5.6K)
    │   │   │                            #   - Summary of all entered data
    │   │   │                            #   - "Generate Blueprint" submit button
    │   │   │
    │   │   └── Step8Regimen.tsx         # Advanced regimen entry (13K)
    │   │                                #   - Compound search with autocomplete
    │   │                                #   - Dose, frequency, timing selection
    │   │                                #   - Rx vs OTC toggle
    │   │                                #   - Prescribed by selector
    │   │                                #   - Brand name, start date
    │   │                                #   - Link to conditions
    │   │
    │   ├── dashboard/             # ═══ 14 DASHBOARD WIDGETS ═══
    │   │   │
    │   │   ├── OrganScorecard.tsx          # 4-organ score cards (6.4K)
    │   │   │                               #   - Liver, Kidney, Cardiovascular, Metabolic
    │   │   │                               #   - Score (0-100) with colour coding
    │   │   │                               #   - Risk level badge (green/amber/red)
    │   │   │                               #   - Primary driver annotation
    │   │   │                               #   - 5-year projected score
    │   │   │
    │   │   ├── TrajectoryChart.tsx         # 5-year trajectory (5.8K)
    │   │   │                               #   - Recharts LineChart
    │   │   │                               #   - Baseline vs optimised lines
    │   │   │                               #   - Year 0-5 on x-axis, index 0-100 on y-axis
    │   │   │
    │   │   ├── MultiTimeframeChart.tsx     # Extended multi-organ projection (10.6K)
    │   │   │                               #   - Per-organ tabs
    │   │   │                               #   - 6-month, 1-year, 2-year, 5-year horizons
    │   │   │                               #   - Confidence band visualisation
    │   │   │                               #   - Organ-years-gained summary
    │   │   │
    │   │   ├── BiologicalAgeWidget.tsx     # Bio age display (6.7K)
    │   │   │                               #   - Chronological vs biological age
    │   │   │                               #   - Delta indicator (+/- years)
    │   │   │                               #   - Visual age comparison
    │   │   │
    │   │   ├── RiskSummaryCard.tsx         # Headline risk summary (3.6K)
    │   │   │                               #   - Risk level with colour badge
    │   │   │                               #   - Liver index score
    │   │   │                               #   - Projected decline percentage
    │   │   │                               #   - Headline text
    │   │   │
    │   │   ├── RecommendationFeed.tsx      # AI recommendation cards (7K)
    │   │   │                               #   - Action type badges (swap/reduce/add/behaviour)
    │   │   │                               #   - Gemini-enriched details text
    │   │   │                               #   - Expected improvement deltas
    │   │   │                               #   - Confidence scores
    │   │   │                               #   - Evidence reference links
    │   │   │                               #   - "Adopt" toggle per recommendation
    │   │   │
    │   │   ├── CompoundCart.tsx            # Current regimen display (4.7K)
    │   │   │                               #   - List of all compounds with doses
    │   │   │                               #   - Per-compound load annotation
    │   │   │                               #   - Protective vs harmful indicator
    │   │   │
    │   │   ├── CompoundContributions.tsx   # Per-compound load breakdown (2.3K)
    │   │   │                               #   - Sorted by load (highest first)
    │   │   │                               #   - Load points visualised as bars
    │   │   │
    │   │   ├── PathwayChainPanel.tsx       # Drug→Gene→Pathway chains (7.2K)
    │   │   │                               #   - Per-compound gene interaction details
    │   │   │                               #   - CYP phenotype × multiplier
    │   │   │                               #   - Pathway chain flow visualisation
    │   │   │                               #   - Per-organ impact breakdown
    │   │   │
    │   │   ├── GuidelinePanel.tsx          # Clinical guidelines (5K)
    │   │   │                               #   - CPIC, AHA, WHO guideline references
    │   │   │                               #   - Organ-specific recommendations
    │   │   │
    │   │   ├── CircadianPanel.tsx          # Circadian / sleep analysis (5.1K)
    │   │   │                               #   - Sleep quality metrics
    │   │   │                               #   - Circadian rhythm assessment
    │   │   │
    │   │   ├── ClinicianExportButton.tsx   # PDF download button (2.8K)
    │   │   │                               #   - Calls GET /export/clinical-pdf
    │   │   │                               #   - Triggers browser download
    │   │   │
    │   │   ├── PaywallOverlay.tsx          # Pro feature overlay (4.4K)
    │   │   │                               #   - Feature preview with blur effect
    │   │   │                               #   - Upgrade CTA
    │   │   │
    │   │   └── ProgressChart.tsx           # Health progress tracking (3.2K)
    │   │                                   #   - Historical score trends
    │   │
    │   ├── notifications/             # ═══ NOTIFICATION SYSTEM ═══
    │   │   └── NotificationBell.tsx        # Bell icon + unread badge + dropdown (included in AppHeader)
    │   │
    │   └── chat/                      # ═══ AI CHAT INTERFACE ═══
    │       └── (chat components)           # Gemini-powered conversational UI
    │
    ├── store/                         # ═══ ZUSTAND STATE STORES ═══
    │   │
    │   ├── wizardStore.ts             # Main application state (182 lines, 6.2K)
    │   │                              #   - step: current wizard step (1-9)
    │   │                              #   - patient, conditions, lifestyle, genetics, regimen,
    │   │                              #     labs, food: all wizard form data
    │   │                              #   - analysisResult: AnalysisResponse | null
    │   │                              #   - adoptedRecs: Set<string> — user-adopted recommendations
    │   │                              #   - Actions: updatePatient, addCondition, addCompound, etc.
    │   │                              #   - loadPriyaExample(): loads canonical demo data
    │   │                              #   - resetWizard(): clears all state
    │   │                              #   NOT persisted (resets on page reload)
    │   │
    │   ├── authStore.ts               # Auth state (102 lines, 3.4K)
    │   │                              #   - token: JWT string | null
    │   │                              #   - user: AuthUser (id, email, full_name, onboarding_complete)
    │   │                              #   - isAuthenticated: boolean
    │   │                              #   - login(email, password): POST /users/login
    │   │                              #   - register(email, password, full_name): POST /users/register
    │   │                              #   - logout(): clears token + user
    │   │                              #   PERSISTED to localStorage (key: "eirion-auth")
    │   │
    │   └── notificationStore.ts       # Notification state (2.9K)
    │                                  #   - Notification list + unread count
    │                                  #   - Fetch, mark as read actions
    │
    ├── api/                           # ═══ API LAYER ═══
    │   ├── analysis.ts                # Analysis API hooks (POST /analysis/run)
    │   └── mock_response.json         # Client-side fallback for offline/demo mode
    │
    ├── data/                          # ═══ STATIC DATA ═══
    │   └── priya.ts                   # Priya demo persona — pre-filled patient data
    │
    └── assets/                        # ═══ STATIC ASSETS ═══
        └── (images, icons)
```

---

## Getting Started

### Prerequisites

- Node.js 20+
- npm 10+

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

> 🟢 **App available at:** `http://localhost:5173`

### Build

```bash
npm run build     # TypeScript check + Vite production build → dist/
npm run preview   # Preview production build locally
```

### Lint

```bash
npm run lint      # ESLint with TypeScript rules
```

---

## Pages

| Route | Component | Auth | Description |
|-------|-----------|:----:|-------------|
| `/` | `SmartHome` → `Landing` | ❌ | Landing page (auto-redirects authenticated users with results to `/dashboard`) |
| `/login` | `Login` | ❌ | Email + password login form |
| `/register` | `Register` | ❌ | Registration form |
| `/demo` | `Demo` | ❌ | Pre-filled Priya demo (no API call needed) |
| `/onboarding` | `Wizard` | ✅ | 9-step onboarding wizard |
| `/dashboard` | `Dashboard` | ✅ | Full analysis dashboard (14 widgets) |
| `/profile` | `ProfileSettings` | ✅ | User profile, password, data export |

---

## Components

### Wizard Components (13)

| Step | Component | Collects |
|------|-----------|----------|
| 1 | `Step1Demographics` | Age, sex, weight, height, ethnicity |
| 2 | `Step2Conditions` | Pre-existing conditions with severity |
| 2b | `Step2Genetics` | Basic genetic info |
| 3 | `Step3GeneticUpload` | 23andMe `.txt` file → CYP phenotype inference |
| 3b | `Step3Lifestyle` | Basic lifestyle parameters |
| 3c | `Step3Diet` | Diet type, calories, macros |
| 4 | `Step4GeneticManual` | Manual CYP metabolizer selections (7 enzymes + MTHFR) |
| 4b | `Step4Regimen` | Basic supplement/medication entry |
| 5 | `Step5LabUpload` | Lab report image → Gemini Vision OCR |
| 5b | `Step5Labs` | Manual lab value entry (16 markers) |
| 6 | `Step6Lifestyle` | Deep lifestyle intake (15 parameters) |
| 6b | `Step6Confirm` | Review all data + submit |
| 8 | `Step8Regimen` | Advanced regimen with timing, Rx flag, brand |

### Dashboard Widgets (14)

| Widget | Data Source | Purpose |
|--------|-----------|---------|
| `OrganScorecard` | `organ_scores[]` | 4-organ health score cards with risk colours |
| `TrajectoryChart` | `trajectory[]` | 5-year baseline vs optimised line chart |
| `MultiTimeframeChart` | `multi_organ_projection` | Extended multi-organ, multi-horizon projections |
| `BiologicalAgeWidget` | `biological_age` | Bio age vs chronological age comparison |
| `RiskSummaryCard` | `risk_summary` | Headline risk level and projected decline |
| `RecommendationFeed` | `recommendations[]` | Gemini-enriched advice cards with adopt toggles |
| `CompoundCart` | wizard regimen | Current medication/supplement stack |
| `CompoundContributions` | `contributions[]` | Per-compound organ load breakdown |
| `PathwayChainPanel` | `compound_gene_chains[]` | Drug→Gene→Pathway→Organ chain visualisation |
| `GuidelinePanel` | `multi_organ_projection` | CPIC/AHA/WHO clinical guideline references |
| `CircadianPanel` | wizard lifestyle | Sleep and circadian rhythm analysis |
| `ClinicianExportButton` | API call | PDF download trigger |
| `PaywallOverlay` | user.is_pro | Pro feature paywall |
| `ProgressChart` | trajectory history | Health progress tracking over time |

---

## State Management

### Zustand Stores

| Store | Persisted | Key State |
|-------|:---------:|-----------|
| `wizardStore` | ❌ | All wizard form data + `analysisResult` + `adoptedRecs` |
| `authStore` | ✅ (localStorage) | JWT token + user profile + `isAuthenticated` |
| `notificationStore` | ❌ | Notification list + unread count |

### Data Flow

```
1. User fills wizard steps → wizardStore updates
2. User submits → Wizard.tsx builds AnalysisRequest from store
3. POST /analysis/run → backend processes → returns AnalysisResponse
4. wizardStore.setResult(response) → stores full response
5. Navigate to /dashboard → Dashboard reads from wizardStore.analysisResult
6. Each widget reads its specific slice of the response
```

---

## Type System

All types are defined in [`src/types.ts`](src/types.ts) (249 lines) and **mirror the backend Pydantic models exactly**:

| Type | Backend Model | Fields |
|------|--------------|--------|
| `Patient` | `models.request.Patient` | age, sex, weight_kg, height_cm, ethnicity |
| `Condition` | `models.request.Condition` | condition_id, severity, diagnosed |
| `Genetics` | `models.request.ExtendedGenetics` | 7 CYP enzymes + MTHFR + diplotypes + source |
| `LifestyleIntake` | `models.request.LifestyleIntake` | 15 lifestyle parameters |
| `Food` | `models.request.Food` | calories, processed %, meat, fiber, diet type |
| `RegimenItem` | `models.request.RegimenItem` | compound, dose, frequency, timing, Rx, brand |
| `Labs` | `models.request.Labs` | 16 lab markers + metadata |
| `AnalysisRequest` | `models.request.AnalysisRequest` | Root request combining all above |
| `AnalysisResponse` | `models.response.AnalysisResponse` | Full response with all scoring data |
| `OrganScore` | `models.response.OrganScore` | organ, score, risk_level, primary_driver |
| `DDIFlag` | `models.response.DDIFlag` | compound pair, mechanism, recommendation |
| `MultiOrganProjection` | `models.response.MultiOrganProjection` | 4-organ multi-timeframe trajectories |

---

## API Integration

### Backend Connection

The API base URL is configured via the `VITE_API_URL` environment variable:

```bash
VITE_API_URL=http://localhost:8000  # default
```

### Auth Flow

```
Register/Login → Server returns { token, user }
       ↓
authStore persists token to localStorage
       ↓
All subsequent API calls include: Authorization: Bearer <token>
       ↓
Auto-logout: 5-min interval checks JWT expiry (App.tsx)
```

### Key API Calls

| Action | Method | Endpoint | Store |
|--------|--------|----------|-------|
| Register | `POST` | `/users/register` | `authStore.register()` |
| Login | `POST` | `/users/login` | `authStore.login()` |
| Run analysis | `POST` | `/analysis/run` | `wizardStore.setResult()` |
| Parse labs | `POST` | `/extraction/parse-labs` | `wizardStore.updateLabs()` |
| Download PDF | `GET` | `/export/clinical-pdf` | Browser download |
| Chat | `POST` | `/chat/message` | Local state |

---

## Build & Deployment

### Vite Configuration

Key settings in [`vite.config.ts`](vite.config.ts):

- **Plugins:** `@vitejs/plugin-react` + `@tailwindcss/vite`
- **Path alias:** `@` → `./src`
- **Chunk splitting:** vendor (React/Router), charts (Recharts), icons (Lucide), auth (Clerk), utils (Axios/Zustand)
- **Chunk size warning:** 600 KB

### Docker (Production)

The Dockerfile uses a **multi-stage build**:

1. **Stage 1 (Builder):** `node:20-slim` — `npm ci` + `npm run build`
2. **Stage 2 (Runner):** `nginx:alpine` — serves `dist/` with SPA fallback

```bash
# Build
docker build -t eirion-frontend \
  --build-arg VITE_API_URL=http://your-backend:8000 .

# Run
docker run -p 5173:80 eirion-frontend
```

Nginx config includes:
- SPA fallback (`try_files $uri $uri/ /index.html`)
- Gzip compression for CSS/JS/JSON
- `/api/` returns 404 (API calls go directly to backend)

---

## Dependencies

### Production

| Package | Version | Purpose |
|---------|---------|---------|
| **react** | 19.2 | UI framework |
| **react-dom** | 19.2 | DOM rendering |
| **react-router-dom** | 7.13 | Client-side routing (7 routes) |
| **zustand** | 5.0 | Lightweight state management (3 stores) |
| **axios** | 1.14 | HTTP client for API calls |
| **recharts** | 3.8 | Charting library (trajectory, projections) |
| **framer-motion** | 12.38 | Animations and transitions |
| **lucide-react** | 1.7 | Icon library |
| **react-hot-toast** | 2.6 | Toast notifications |
| **clsx** | 2.1 | Conditional classname utility |
| **tailwind-merge** | 3.5 | Tailwind class conflict resolution |
| **@clerk/clerk-react** | 5.61 | Auth UI components (optional) |

### Development

| Package | Version | Purpose |
|---------|---------|---------|
| **vite** | 8.0 | Build tool |
| **typescript** | 5.9 | Type checking |
| **tailwindcss** | 4.2 | Utility-first CSS |
| **@tailwindcss/vite** | 4.2 | Tailwind Vite plugin |
| **@vitejs/plugin-react** | 6.0 | React Vite plugin |
| **eslint** | 9.39 | Code linting |
| **eslint-plugin-react-hooks** | 7.0 | React hooks lint rules |
| **eslint-plugin-react-refresh** | 0.5 | Fast refresh lint rules |
| **@types/react** | 19.2 | React type definitions |
| **@types/react-dom** | 19.2 | React DOM type definitions |

### Scripts

```json
{
  "dev": "vite",              // Start dev server (HMR)
  "build": "tsc -b && vite build",  // Type check + production build
  "lint": "eslint .",          // Run ESLint
  "preview": "vite preview"    // Preview production build
}
```

---

<div align="center">

*Part of the [EIRION Precision Longevity Platform](../README.md)*

</div>
