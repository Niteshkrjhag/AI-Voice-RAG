# 🚀 Production Voice AI & RAG Architecture (2026 Assessment)

Welcome! This repository contains a full-stack, enterprise-ready Voice AI architecture, engineered for the 2026 AI Engineer Assessment.

Whether you are a Junior Developer (SDE-1) or a Principal Engineer reviewing system design, this guide explains exactly **what** the project does, **how** it is structured, the **advanced engineering challenges** we conquered, and how to run it.

---

## 📖 Executive Summary

We built a real-time AI Voice Assistant for a Health Insurance company. 

Instead of waiting on hold, customers talk to an AI agent that can instantly retrieve exact policy details and gracefully handle frustrated callers. The system is split into four primary pillars:
1. **The Voice Agent (Vapi):** Handles the telephony and conversation flow.
2. **The Knowledge Base (RAG):** A Qdrant vector database filled with scraped and cleaned policy documents.
3. **Multilingual Routing:** Separate agent configurations for the Philippines (Taglish) and Indonesia (Bahasa), fully connected to the knowledge base.
4. **Live Insights Pipeline:** A background WebSocket server that streams audio to AssemblyAI and uses Gemini to detect customer frustration, popping up real-time UI nudges for human supervisors.

---

## 🏗 System Architecture & Flow Diagram

Here is a high-level overview of how data flows through the system during an active phone call:

```mermaid
graph TD
    %% Define Styles
    classDef external fill:#f9f,stroke:#333,stroke-width:2px;
    classDef backend fill:#bbf,stroke:#333,stroke-width:2px;
    classDef database fill:#bfb,stroke:#333,stroke-width:2px;
    classDef frontend fill:#fbb,stroke:#333,stroke-width:2px;

    %% Actors and Telephony
    User((🗣️ Customer)) -->|Speaks| Vapi[📞 Vapi Voice Platform]
    
    %% Main RAG Flow
    Vapi -->|Custom Tool Request| FastAPI[⚙️ FastAPI RAG Server]
    FastAPI -->|Semantic Search| Qdrant[(📚 Qdrant Vector DB)]
    Qdrant -->|Policy Documents| FastAPI
    FastAPI -->|JSON Response| Vapi
    Vapi -->|Speaks Answer| User
    
    %% Data Ingestion Flow (Offline)
    Crawler[🕷️ Crawl4AI] --> Cleaner[🧹 Data Cleaner & PII Redactor]
    Cleaner --> Chunker[✂️ Semantic Chunker]
    Chunker --> Embedder[🧠 SentenceTransformer]
    Embedder -->|Upsert Vectors| Qdrant
    
    %% Live Insights Flow
    Vapi -.->|Audio Fork| StreamServer[🎧 FastAPI Stream Server]
    StreamServer -->|WebSocket| AAI[🎙️ AssemblyAI ASR]
    AAI -->|Live Transcripts| StreamServer
    StreamServer -->|Extract Signals| Gemini[🧠 Gemini 2.0 Flash]
    Gemini -->|Frustration/Sales| Nudge[🚨 Nudge Engine]
    Nudge -->|WebSocket Push| Dashboard[💻 Web UI Dashboard]
    
    %% Apply Styles
    class Vapi,AAI,Gemini,Crawler external;
    class FastAPI,StreamServer,Cleaner,Chunker,Embedder,Nudge backend;
    class Qdrant database;
    class Dashboard frontend;
```

---

## 🛠 How to Set Up and Run the Code

Follow these steps to bootstrap the project on your local machine.

### 1. Installation
Create a Python virtual environment and install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuration (`.env`)
Copy `.env.example` to `.env` and fill in your actual API keys. 
> **Note:** The server enforces strict validation on startup. If you do not provide `RAG_API_KEY`, the server will refuse to boot to prevent silent production crashes.
```bash
cp .env.example .env
```

### 3. Build the Knowledge Base (Q2)
Scrape the fake insurance websites, clean the data, generate embeddings locally, and index them into Qdrant:
```bash
python -m q2_knowledge_base.pipeline
```

### 4. Start the RAG Backend API
Start the FastAPI server that Vapi will call to search the knowledge base:
```bash
python -m uvicorn q2_knowledge_base.api:app --port 8000
```
Use `ngrok` to expose this port to the internet (`ngrok http 8000`), then export the URL:
```bash
export NGROK_URL=https://your-ngrok-url.ngrok.app
```

### 5. Provision the Voice Agents (Q1 & Q3)
Automatically deploy your Voice Agents to the Vapi cloud. This script is idempotent—running it twice will patch the existing bot rather than creating a duplicate.
```bash
# Provision the English Bot
python -m q1_voice_agent.provision

# Provision the Multilingual Bots
python -m q3_multilingual.provision ph   # Philippines (Taglish)
python -m q3_multilingual.provision id   # Indonesia (Bahasa)
```

### 6. Start the Live Insights Dashboard (Q4)
Run the real-time background WebSocket server:
```bash
python q4_live_insights/server.py
```
Open `http://localhost:8080` in your browser and click **Start Simulated Call** to watch live AI nudges populate.

---

## 🛡️ Problems Faced & Engineering Solutions (SDE-3 Deep Dive)

While building this architecture, we ran into severe distributed-systems and concurrency challenges. Here is how we solved them to achieve Enterprise Grade stability:

### 1. Vector Database Duplication (Idempotency)
* **The Problem:** Python's built-in `hash()` function uses a randomized seed per process. When generating chunk IDs for Qdrant, a new UUID was created every time the pipeline ran, causing massive vector duplication.
* **The Solution:** We replaced `hash()` with deterministic MD5 hashing (`hashlib.md5(doc['url'].encode()).hexdigest()`), ensuring Qdrant safely overwrites existing documents instead of duplicating them.

### 2. FastAPI Event Loop Freezing (Concurrency)
* **The Problem:** In our RAG API, generating local sentence embeddings (CPU-bound) and querying Qdrant (Network-bound) blocked the entire Python AsyncIO event loop, causing `504 Gateway Timeouts` when multiple phone calls queried the database simultaneously.
* **The Solution:** We wrapped all synchronous bottlenecks in `await asyncio.to_thread()`, pushing the heavy lifting to OS background threads and keeping the FastAPI web server completely non-blocking.

### 3. Unbounded AI Memory Leaks (State Management)
* **The Problem:** In the Live Insights pipeline, appending every spoken word to a single `full_context` string over a 45-minute phone call caused Gemini API context-window exhaustion and exponential token costs.
* **The Solution:** We implemented a sliding memory window, truncating the context strictly to the last 4,000 characters. The LLM retains immediate context without leaking memory.

### 4. Background Webhook DDoS (Rate Limiting)
* **The Problem:** Clicking "Start Simulated Call" in the dashboard multiple times launched parallel background tasks processing the exact same audio stream, spamming the UI and instantly triggering Gemini `429 Rate Limits`.
* **The Solution:** We implemented a global `is_streaming` state lock on the FastAPI endpoint to reject overlapping requests with a `409 Conflict`.

### 5. Silent InfoSec and Configuration Failures
* **The Problem:** Vapi Custom Tools originally hardcoded the `X-API-Key` directly in the source code. Furthermore, missing `.env` keys caused silent runtime crashes deep in the application.
* **The Solution:** We injected `RAG_API_KEY` directly from the environment into the tool payload. We also added a fast-fail `validate()` method to `shared/config.py` that immediately crashes the application on boot if security keys are missing.

### 6. RAG Hallucinations & Multilingual Disconnection
* **The Problem:** 
    1. Qdrant returned slightly relevant documents for completely unrelated questions (e.g. "car loans"), causing the bot to hallucinate.
    2. The multilingual bots were missing the Vapi `tools` array entirely, disconnecting them from the RAG database.
* **The Solution:** We enforced a strict `score_threshold=0.3` in the Qdrant retrieval layer to instantly reject low-confidence matches. We then refactored the Q3 config schemas to dynamically inject the Custom Tool schema, allowing Taglish and Bahasa speakers to successfully execute vector database queries.

---

## 📂 Project Structure

```text
├── .env.example             # Environment variable template
├── requirements.txt         # Pinned Python dependencies
├── shared/                  
│   ├── config.py            # Centralized configuration with fast-fail validation
│   └── logger.py            # JSON structured logging (structlog)
├── q1_voice_agent/          
│   ├── provision.py         # Idempotent Vapi deployment script
│   ├── system_prompt.py     # Base rules & Prompt Injection defenses
│   └── tools.py             # JSON Schema for FastAPI Custom Tools
├── q2_knowledge_base/       
│   ├── scraper.py           # Async Crawl4AI ingestion
│   ├── cleaner.py           # PII redaction and boilerplate removal
│   ├── chunker.py           # Semantic chunking with deterministic UUIDs
│   ├── embedder.py          # Generator batching (OOM proof) SentenceTransformers
│   └── api.py               # Secure FastAPI Retrieval Endpoint
├── q3_multilingual/         
│   ├── provision.py         # CLI deployment router for regions
│   ├── philippines/         # Taglish Agent config and prompts
│   └── indonesia/           # Bahasa Agent config and prompts
└── q4_live_insights/        
    ├── server.py            # Concurrency-locked WebSocket Server
    ├── pipeline.py          # AssemblyAI and Gemini Orchestrator
    ├── signal_extractor.py  # LLM prompt wrapper with backoff retries
    ├── nudge_engine.py      # Cooldown and suppression logic
    └── templates/dashboard.html # Auto-reconnecting frontend UI
```
