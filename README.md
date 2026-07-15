<div align="center">
  
# ⏳ Project Kairos

**Your Local, Privacy-First AI Career Architect.**

*Automate the drudgery. Deconstruct the ATS. Pass the interview.*

</div>

---

## 🦅 The Vision

The modern job hunt is broken, soul-crushing, and exhausting. Engineers waste hundreds of hours fighting through broken ATS filters, writing redundant cover letters, managing disjointed email threads, and guessing how to optimize their profiles. 

**Kairos is the lifesaver we all needed.** 

It acts as an autonomous career agent that lives on your host machine, ensuring your data never leaks to third-party servers. It automates the mechanical drudgery of the job hunt so you can focus on what actually matters: passing the interview. 

---

## ✨ Core Workflows

### 1. The Frictionless Setup
Kairos instantly diagnoses your hardware (RAM/VRAM) to dynamically route AI processing locally (via Ollama/Llama-3) or to the cloud (via Gemini BYOK), ensuring lightning-fast performance regardless of your machine.

### 2. The Master Social Audit & Cohesion Score
Kairos scrapes and evaluates your digital footprint. 
- **LinkedIn Optimization:** Analyzes your headline for recruiter hooks, ensures custom URL setups, and provides personalized weekly posting strategies.
- **GitHub Strategy:** Intelligently recommends exactly which repositories to pin based on technical complexity and live-hosted links.
- **The Cohesion Score:** A unified metric that constantly evaluates how perfectly your Resume, LinkedIn, and GitHub align with each other.

### 3. State-of-the-Art ATS Optimization
Uses deep semantic similarity (local vector embeddings) combined with exact boolean matching to simulate enterprise ATS systems (like Workday). It finds your resume's weaknesses and uses the LLM to seamlessly patch those exact gaps via an interactive UI.

### 4. Skill Gap Analysis & Roadmaps
Kairos cross-references your resume against scraped market data to identify missing skills. It then generates a prioritized, step-by-step learning roadmap (specifying exact depth required) so you learn exactly what is needed to get hired without falling into a "tutorial hell" trap.

### 5. Volume + Precision Hunting & Tracking
- **Scraping:** Scrapes standard job boards and quietly *monitors the official internal career portals of MNCs (Google, Microsoft, etc.)*. 
- **The Kanban Board:** A local SQLite-powered visual dashboard where you can effortlessly track the status of all your applications (Applied, Interviewing, Offered).

### 6. The Interview Loop
Connects to local Gmail OAuth2 to quietly monitor recruiter emails, truncating long HTML chains to save tokens, and drafting polished, context-aware replies directly into your Drafts folder.

### 7. The Feedback Loop
A built-in user UI that securely packages bug reports, feature requests, and non-invasive telemetry into a clean email sent directly to the developer's inbox for continuous product improvement.

---

## 🏗️ Architecture

Kairos is a decoupled monorepo optimized for local desktop execution.

### Frontend
A vibrant, light, and minimalist application. The UI aims to reduce job-hunt anxiety using clean aesthetics and charming, subtle animal illustrations, while maintaining a deeply professional user experience. 
> **Tech Stack:** `Electron`, `React (TypeScript)`, `Vite`, `TailwindCSS`

### Backend
A robust background server executing deterministic logic, vector scoring, and data scraping.
> **Tech Stack:** `Python`, `FastAPI`, `SQLite3`, `SQLModel`, `uv`

### AI Pipeline & NLP
Built to force the LLM to output mathematically strict JSON schemas, guaranteeing deterministic data flow to the UI.
> **Tech Stack:** `Pydantic`, `Instructor`, `Ollama` (Local Llama-3), `spaCy`, `SentenceTransformers`

---

## 🚀 Getting Started

*(Installation instructions, local setup, and contribution guidelines will be added prior to the v1.0 release.)*

<div align="center">
  
*Architected and Built for Engineers, by Engineers.*

</div>
