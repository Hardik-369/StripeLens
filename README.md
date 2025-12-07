# StripeLens 🧠💳

**The 50-Line AI Financial Analyst for Your Webhooks**

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg) ![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.95%2B-green)

StripeLens is a **minimalist, drop-in microservice** that transforms cryptic Stripe webhook events into clear, actionable business insights using the power of OpenRouter's open-source LLMs.

> "Stop guessing why payments failed. Start knowing what to do next."

---

## ✨ Features

- **🚀 Instant Analysis**: Converts JSON blobs into human-readable executive summaries.
- **🛡️ Root Cause Detection**: Identifies exactly *why* a transaction failed (e.g., "Generic Decline" vs. "Insufficient Funds").
- **🚦 Smart Impact Scoring**: Automatically categorizes events as **Low**, **Medium**, or **High** priority.
- **💡 Actionable Advice**: Generates specific next steps for your support team (e.g., "Email customer X to update card").
- **⚡ Zero Bloat**: No database. No complex auth. Just one file.

---

## 🛠️ Tech Stack

- **FastAPI**: For high-performance async handling.
- **OpenRouter (Amazon Nova 2 Lite)**: efficient, cost-effective LLM intelligence.
- **Pydantic**: Robust data validation and schema enforcement.

---

## 🚀 Quick Start

### 1. Requirements
- Python 3.10+
- An [OpenRouter](https://openrouter.ai) API Key

### 2. Installation
```bash
git clone https://github.com/yourusername/StripeLens.git
cd StripeLens
pip install -r requirements.txt
```

### 3. Usage
Set your key and run the server:
```bash
# Linux/Mac
export OPENROUTER_API_KEY=sk-or-v1-...
python main.py

# Windows (PowerShell)
$env:OPENROUTER_API_KEY="sk-or-v1-..."
python main.py
```

### 4. Test It
Send a simulated webhook:
```bash
python test_api.py
```

---

## 🔌 API Reference

### `POST /explain_event`

Accepts a raw Stripe event JSON.

**Sample Request:**
```json
{
  "type": "invoice.payment_failed",
  "data": { ... }
}
```

**Sample Response:**
```json
{
  "event_type": "invoice.payment_failed",
  "summary": "Customer subscription payment of $29.99 failed due to insufficient funds.",
  "root_cause": "insufficient_funds",
  "customer_impact_level": "high",
  "recommended_actions": [
    "Contact customer cus_987 to update payment method.",
    "Retry charge in 3 days."
  ]
}
```

---

## 🤝 Contributing

Keep it simple. If you can do it in fewer lines, PRs are welcome.

## 📄 License

MIT

