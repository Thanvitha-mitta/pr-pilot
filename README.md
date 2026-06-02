# 🤖 PR-Pilot: Autonomous Code Review Agent

**PR-Pilot** is an event-driven, autonomous AI software engineer that intercepts GitHub Pull Requests, performs structural codebase retrieval (RAG), and posts instant, inline code reviews. 

Built to eliminate the bottleneck of manual code reviews, PR-Pilot acts as a first-pass gatekeeper—providing developers with context-aware feedback on logic bugs, security vulnerabilities, and missing edge cases within seconds.

---

## 🏗️ System Architecture

Unlike standard AI chatbots, PR-Pilot is designed as a highly fault-tolerant **State Machine** orchestrated by **LangGraph**, exposed via a **FastAPI** webhook server. This allows the system to process GitHub webhooks asynchronously in the background without HTTP timeouts.

### The Pipeline
1. **Event Trigger:** A developer opens or updates a Pull Request. GitHub fires a webhook payload to the FastAPI endpoint.
2. **Node 1 (Fetch):** The agent authenticates via the PyGithub API and extracts the raw diffs and file paths.
3. **Node 2 (Retrieve / RAG):** The agent queries a **Qdrant** Vector Database to pull surrounding codebase context. *(See Codebase Ingestion below).*
4. **Node 3 (Reason):** The diff and context are fed into **Llama-3.3-70b (via Groq LPUs)**. Strict JSON output is enforced using **Pydantic** to map identified issues to exact line numbers and severities.
5. **Node 4 (Action):** The agent formats the JSON payload into a clean Markdown comment and posts it directly to the GitHub PR.

---

## ✨ Key Features & Engineering Highlights

* **Structural AST Chunking:** Instead of naive character-based text splitting (which destroys code context), the ingestion pipeline uses a custom **Recursive AST Walker via Tree-sitter**. It parses TypeScript/Python code by logical boundaries (functions, classes) ensuring the embedding model understands complete logical blocks.
* **Ultra-Low Latency Inference:** Utilizes the **Groq API** to run Meta's massive 70-billion parameter model at hundreds of tokens per second, ensuring real-time PR feedback.
* **Local Embeddings:** Uses Qdrant's native **FastEmbed** to generate high-quality vector embeddings locally on the CPU, drastically reducing API costs and latency.
* **Asynchronous Webhooks:** Built with FastAPI `BackgroundTasks` to instantly return a `200 OK` to GitHub (preventing webhook timeouts) while the LangGraph agent executes the heavy LLM workflow asynchronously.

---

## 📊 Evaluation & Observability (Mitigating AI Hallucination)

A major challenge in AI code review is "Helpfulness Bias" (the LLM inventing minor nitpicks on perfect code just to provide an answer). 

* **Eval Harness (`evals/run_evals.py`):** The system prompt was iteratively engineered using **Few-Shot Prompting** and tested against a ground-truth dataset of historical PRs. The current iteration achieves **100% System Accuracy** with a 0% False Positive rate on perfect code.
* **LangSmith Tracing:** The entire LangGraph pipeline is instrumented with **LangSmith**. Every node execution, latency metric, token cost, and LLM prompt/response is traced to allow for deterministic debugging of context-retrieval failures.

---

## 🚀 Tech Stack

* **AI / Orchestration:** LangGraph, LangChain, LangSmith
* **Inference:** Llama-3.3-70b (Groq API)
* **Backend:** FastAPI, Uvicorn, Python 3.10
* **Vector DB & RAG:** Qdrant, FastEmbed, Tree-sitter (Abstract Syntax Trees)
* **Integrations:** GitHub REST API, GitHub Webhooks

---

## 🛠️ Local Setup & Execution

### 1. Prerequisites
* Qdrant Database (Running via Docker or Qdrant Cloud)
* Groq API Key
* LangSmith API Key
* GitHub Personal Access Token (Classic, with `repo` scope)

### 2. Environment Variables (`.env`)
```env
GITHUB_TOKEN=ghp_...
GROQ_API_KEY=gsk_...
QDRANT_URL=http://localhost:6333
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_...
LANGCHAIN_PROJECT=pr-pilot
```

### 3. Installation
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Running the Agent
Start the FastAPI Webhook Server:
```bash
uvicorn app.main:app --reload
```

Trigger a test PR (Simulate GitHub Webhook):
```bash
python scripts/test_webhook.py
```

Run the Evaluation Harness (Measure Precision/Recall):
```bash
python evals/run_evals.py
```

---
*Built as a production-ready demonstration of Agentic AI, RAG, and MLOps principles.*