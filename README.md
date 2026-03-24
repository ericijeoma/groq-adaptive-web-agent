# groq-adaptive-web-agent

> A fully local, zero-cost LLM agent that decides — at inference time — whether to answer from model memory or retrieve live structured product data from Amazon. No API keys. No cloud. Runs entirely on your machine.

---

## Overview

Most LLM agent demos require a paid API, cloud infrastructure, or vendor lock-in. This project runs **100% locally and for free** using Ollama — and still delivers a production-grade tool-calling architecture.

The agent uses the **Groq tool-use model** (pulled via Ollama) which is specifically fine-tuned for function/tool calling. When you ask a question, the model decides on its own whether to answer from what it already knows, or invoke the scraping tool to fetch live Amazon product data. No hardcoded rules. No prompt hacks. Real tool-calling, running on your laptop.

```
User query
    │
    ▼
Groq tool-use model (via Ollama — local inference)
    │
    ├── Answer from memory ──────────────────────────► Response
    │
    └── Invoke scrape tool
            │
            ▼
        nodriver + Chromium
            │
            ▼
        Amazon product data
        (title, price, rating)
            │
            ▼
        Model synthesises response ─────────────────► Response
```

---

## Why This Is Impressive

- **Fully local** — Ollama runs the LLM on your own machine. No data leaves your computer
- **Completely free** — no Groq API billing, no OpenAI credits, no cloud costs ever
- **Real tool-calling** — uses a model fine-tuned specifically for function-calling, not a prompted workaround
- **Live structured data** — scrapes real Amazon product listings (titles, prices, ratings) on demand
- **Adaptive retrieval** — the model reasons about when retrieval is needed vs. when memory is enough

---

## Tech Stack

| Layer | Technology | Cost |
|---|---|---|
| Local LLM Inference | [Ollama](https://ollama.com) | Free |
| Tool-calling Model | `llama3-groq-tool-use:8b` via Ollama | Free |
| Browser Automation | [nodriver](https://github.com/ultrafaker/nodriver) | Free |
| Browser | Chromium | Free |
| Language | Python 3.10+ | Free |

---

## Project Structure

```
groq-adaptive-web-agent/
├── agent.py               # Main agent loop — Ollama tool-calling logic
├── scraping_tools.py      # scrape_amazon_product() tool definition
├── test_amazon.py         # Test suite with edge case validation
├── requirements.txt
└── README.md
```

---

## Prerequisites

- Windows 10/11
- Python 3.10 or higher
- [Ollama](https://ollama.com/download) installed
- That's it — no API keys, no accounts, no paid services

---

## Installation (Windows)

### 1. Install Ollama

Download and install from [ollama.com/download](https://ollama.com/download), then open PowerShell and pull the tool-use model:

```powershell
ollama pull llama3-groq-tool-use:8b
```

Wait for the download to complete. Verify it works:

```powershell
ollama run llama3-groq-tool-use:8b "say hello"
```

### 2. Clone the repository

```powershell
git clone https://github.com/ericijeoma/groq-adaptive-web-agent.git
cd groq-adaptive-web-agent
```

### 3. Create and activate a virtual environment

```powershell
python -m venv venv
venv\Scripts\activate
```

### 4. Install dependencies

```powershell
pip install -r requirements.txt
```

> **Note:** Chromium is listed in `requirements.txt` and installs automatically. No separate browser installation needed.

That's it. No `.env` file. No API keys. You're ready to run.

---

## Usage

### Run the agent

```powershell
python agent.py
```

Then type any question:

```
You: What's a good mechanical keyboard under $100?
Agent: [triggers scrape tool → fetches live Amazon results → synthesises response]

You: What is RAG in AI?
Agent: [answers directly from model memory — no scrape triggered, instant response]
```

The model decides which path to take. You don't configure it.

### Run the scraper in isolation

```powershell
# Default search term
python test_amazon.py

# Custom search term
python test_amazon.py "standing desk"
```

---

## Running the Tests

The test suite validates three scenarios on every run:

```powershell
python test_amazon.py
```

| Test Case | Purpose |
|---|---|
| `"mechanical keyboard"` (or custom term) | Happy path — validates all returned fields |
| `"xzqwerty99999zzz"` | No-results edge case — confirms graceful handling |
| `""` (empty string) | Sparse input — confirms no crash on empty query |

Example output:

```
────────────────────────────────────────────────────────────
  [happy path] scrape_amazon_product('mechanical keyboard')
────────────────────────────────────────────────────────────
  Found 5 product(s):

  1. Keychron K2 Wireless Mechanical Keyboard
     Price  : $89.99
     Rating : 4.6

  ✅ All fields validated for 5 product(s)

────────────────────────────────────────────────────────────
  [no results expected] scrape_amazon_product('xzqwerty99999zzz')
────────────────────────────────────────────────────────────
  ⚠  No products found

────────────────────────────────────────────────────────────
  [empty string] scrape_amazon_product('')
────────────────────────────────────────────────────────────
  ⚠  No products found
```

---

## Design Decisions

**Why Ollama instead of a cloud API?**
Ollama runs inference locally — no latency from network calls, no usage costs, no data sent to a third party. The `llama3-groq-tool-use:8b` model is Groq's open-weight tool-calling model, which means you get the same tool-calling capability entirely on your own hardware for free.

**Why the Groq tool-use model specifically?**
Most general-purpose models handle tool-calling unreliably through prompt engineering. The `llama3-groq-tool-use:8b` model is fine-tuned specifically for structured function-calling — it produces consistent, parseable tool invocations rather than freeform text guesses.

**Why nodriver over Selenium or Playwright?**
nodriver is undetected by anti-bot systems, making it significantly more reliable for scraping platforms like Amazon that actively block headless browsers.

---

## Limitations

- First run requires downloading the Ollama model (~4GB depending on variant)
- Inference speed depends on your local hardware (CPU vs GPU)
- Amazon page structure can change; selectors may need updating over time
- Currently returns top N results per search — no pagination

