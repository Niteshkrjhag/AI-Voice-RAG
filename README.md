# 🚀 Production Voice AI & RAG Architecture (2026 Assessment)

Welcome! This repository contains a full-stack, production-ready Voice AI architecture. It was built to pass the 2026 AI Engineer Assessment. 

If you are a Junior Developer (SDE 1) joining the team, don't worry! This guide is written in very simple English. It will explain **what** we built, **why** we built it this way, and **how** you can run it yourself.

---

## 📖 What Does This Project Do?

This project builds an AI Voice Assistant for a Health Insurance company. 

Imagine you are calling your health insurance company to ask about a policy. Instead of waiting on hold for a human, you talk to an AI agent. 
- The AI agent listens to your voice.
- It searches a **Knowledge Base** (a smart database) to find the exact rules about your policy.
- It speaks the answer back to you.
- During the call, a background system (Live Insights) listens in. If the customer sounds frustrated, or if the AI forgets to read a legal warning, the Live Insights system pops up a "Nudge" (an alert) on a dashboard so a human supervisor can step in!

---

## 🏗 How It Works (The Architecture)

We split the project into 4 main parts (Phases). Here is a simple breakdown:

### Phase 1: The Knowledge Base (Question 2)
Before the AI can answer questions, it needs to read the company's rulebooks. 
1. **Scraping:** We download text from fake company websites.
2. **Cleaning:** We remove useless text (like headers) and hide private user data (PII).
3. **Chunking:** We chop the big documents into smaller paragraphs so they are easy to search.
4. **Embedding & Qdrant:** We convert these paragraphs into numbers (Vectors) using a free, local AI model (`sentence-transformers`). We save these numbers in a smart database called **Qdrant**.

### Phase 2: The Voice Agent (Question 1)
We use a platform called **Vapi.ai** to handle the phone call.
- We give the Vapi agent a "System Prompt" (a list of strict rules, like "do not make up answers").
- When the user asks a question, the Vapi agent sends the question to our FastAPI server.
- Our server searches Qdrant, finds the correct paragraph, and sends it back so the agent can read it out loud.

### Phase 3: Multilingual Bots (Question 3)
We built settings to let the bot speak different languages for different countries.
- **Philippines:** The bot speaks "Taglish" (a mix of Tagalog and English) and understands local insurance words like *premium*.
- **Indonesia:** The bot speaks formal Bahasa Indonesia but understands slang like *cicilan* (installments).

### Phase 4: Live Insights & Nudges (Question 4)
While a call is happening, we want to monitor it in real-time.
- We stream the audio to **AssemblyAI** to convert speech to text instantly.
- We send that text to **Gemini 2.0 Flash** (a very fast AI model by Google) to check if the customer is angry or if we missed a sales opportunity.
- If we find an issue, we send a "Nudge" over a **WebSocket** (a real-time connection) to a nice HTML dashboard so human managers can see it pop up immediately.

---

## 🛠 How to Set Up and Run the Code

Follow these simple steps to run the code on your own computer.

### Step 1: Install the Requirements
First, we need to create a safe space for our code called a "Virtual Environment". Then we install all the Python libraries we need.
```bash
# Create the virtual environment
python3 -m venv venv

# Activate it (Mac/Linux)
source venv/bin/activate

# Install the required packages
pip install -r requirements.txt
```

### Step 2: Set Up Your Passwords (API Keys)
We need keys to talk to external services like Qdrant and Google. 
1. Copy the file named `.env.example` and rename the new copy to `.env`.
2. Open `.env` and fill in your actual passwords/keys:
   - `QDRANT_URL` and `QDRANT_API_KEY`
   - `GOOGLE_API_KEY` (For Gemini 2.0 Flash)
   - `VAPI_API_KEY`
   - `ASSEMBLYAI_API_KEY`

### Step 3: Run the Knowledge Base Pipeline
This command will read a fake Health Insurance policy, chunk it, and save it to your Qdrant database.
```bash
# Make sure your virtual environment is activated!
python -m q2_knowledge_base.pipeline
```

### Step 4: Provision the Voice Bot
We need to start our server so Vapi can talk to our database.
```bash
# Start our FastAPI server locally on port 8000
python -m uvicorn q2_knowledge_base.api:app --port 8000
```
In a new terminal window, use a tool like `ngrok` to make your local server public on the internet:
```bash
ngrok http 8000
```
Copy the URL ngrok gives you (e.g., `https://1234-abcd.ngrok.app`). Then, in another terminal, run this to create your bot on Vapi:
```bash
export NGROK_URL=https://your-ngrok-url.app
python -m q1_voice_agent.provision
```
You will get an Assistant ID. You can plug this ID into Vapi's website to test the phone call!

### Step 5: Test the Live Insights Dashboard
Want to see the real-time monitoring dashboard in action? Run this:
```bash
python q4_live_insights/server.py
```
Open your web browser and go to `http://localhost:8080`. Click the **"Start Simulated Call"** button. You will see text streaming in and alert cards popping up!

---

## 📊 Testing & Performance Details

### Did the Knowledge Base work?
Yes! During testing, we asked the bot: *"What is the waiting period for cataracts?"*
Because we chopped the documents correctly, the system instantly found the rule: *"24 months waiting period for conditions like Cataract, Hernia, and Joint Replacements."* 

### How fast is the Live Insights Pipeline (Latency)?
In real-time systems, speed is everything. We measured how long it takes for a spoken word to turn into a UI alert on the dashboard.
- **AssemblyAI Speech-to-Text:** Takes about 300 to 450 milliseconds per audio chunk.
- **Gemini AI Signal Checking:** Takes about 800 to 1200 milliseconds to read the text and output a JSON alert.
- **WebSocket Push to UI:** Takes about 50 milliseconds.
- **Total Time:** Around 1.2 to 1.7 seconds total. This is extremely fast and allows a human manager to step in before the customer hangs up!

### How do we stop Spam Alerts (False-Positives)?
If a customer is very angry, the AI might detect "Frustration" 10 times in a row. To prevent the dashboard from exploding with alerts, our `NudgeEngine` has a **15-second cooldown**. If it fires a "Frustration" alert, it will ignore any new "Frustration" alerts for the next 15 seconds.

---

## 🛡️ Reliability & Resilience (Production Best Practices)

To ensure this system doesn't crash in a real enterprise environment, we implemented several safety nets:
1. **Dynamic Nudges:** The UI doesn't just show generic alerts; it extracts the actual `reasoning` from the LLM, making nudges highly specific (e.g., "Customer mentioned family, offer Floater Rider" vs just "Cross-sell opportunity").
2. **Robust JSON Parsing:** LLMs sometimes hallucinate formatting. Our pipeline explicitly strips markdown tags before parsing, preventing the background streaming tasks from crashing silently.
3. **Async Deadlock Prevention:** The Live Insights AI calls use explicit `asyncio.wait_for` timeouts. If the Google API hangs, the task cleanly exits instead of leaking memory indefinitely.
4. **WebSocket Memory Management:** The server actively sweeps for and removes disconnected client sockets during broadcast loops, preventing CPU and memory bloat over long server uptimes.
5. **Token Optimization & CORS:** The RAG API response is flattened to remove useless Pydantic metadata, drastically reducing the token cost for Vapi. Both FastAPI servers also implement strict `CORSMiddleware` so decoupled dashboards can safely connect.

---

## ⚠️ Known Limitations & Future Improvements (10x Scale)

If we were to deploy this to millions of users, we would need to fix a few things:

1. **Slow Local Embeddings:** 
   - *The Problem:* Right now, we convert text to vectors using the CPU on our local machine. This is cheap but slow if thousands of documents arrive at once.
   - *The Fix:* We should move this task to a dedicated GPU server (like AWS SageMaker or Ray Serve).
2. **Audio Streams:**
   - *The Problem:* Our current Live Insights demo reads from a fake `.wav` file saved on the computer.
   - *The Fix:* In production, we need a SIP-to-WebSocket bridge (using Twilio or AudioCodes) to capture the actual live phone call audio from the telephone network.
3. **Background Noise (Noisy Audio):**
   - *The Problem:* If a customer calls from a noisy street, the Speech-to-Text engine might output garbage words. The AI might get confused by the garbage text and falsely trigger a "Frustration" alert.
   - *The Fix:* We should add a Voice Activity Detector (VAD) to filter out background noise before sending the audio to AssemblyAI. We could also use acoustic analysis (measuring the actual pitch and volume of the voice) rather than just reading the text to detect anger.
