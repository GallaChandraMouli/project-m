# NexusCompute: Decentralized GPU AI Inference Marketplace

[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Node: 18+](https://img.shields.io/badge/Node-18%2B-green.svg)](https://nodejs.org/)
[![API: OpenAI Compatible](https://img.shields.io/badge/API-OpenAI%20Compatible-emerald.svg)](http://localhost:8000/docs)

**NexusCompute** is a high-performance, hybrid decentralized AI inference network inspired by modern compute protocols like **Antseed**. It turns consumer and enterprise GPUs (RTX 3090/4090, Apple Silicon M-series, A100/H100) into revenue-generating inference endpoints, allowing developers to query open-source AI models (Llama 3, DeepSeek-R1, Mistral, Qwen) with drop-in OpenAI SDK compatibility at 50–80% lower cost.

---

## 🚀 Key Modern Architectural Highlights

- **Outbound-Only WebSocket Uplink**: Provider nodes connect outbound to the coordinator. **Zero open ports, dynamic DNS, or firewall port-forwarding needed.**
- **Local Engine Agnostic**: Automatically discovers models from local **Ollama** (`http://localhost:11434`), **vLLM** (`http://localhost:8000`), or built-in test emulation.
- **Smart Latency & Cost Router**: Automatically dispatches inference queries to the lowest-price, lowest-latency active provider with instant failover retry if a node disconnects.
- **Drop-in OpenAI Compatibility**: Works natively with the official OpenAI Python/Node.js SDKs, LangChain, Cursor, Claude Code, and cURL via `http://localhost:8000/v1`.
- **Verifiable Micro-Billing Ledger**: Real-time token counting with escrow pre-authorization, debiting consumers and crediting 90% of earnings to providers while taking a 10% protocol cut.
- **Modern Cyberpunk / Minimalist Dark UI**: Complete web portal featuring a Live Marketplace Explorer, Real-time Streaming Chat Playground with TTFT & tok/s telemetry HUD, API Key Manager, and Provider Rig Dashboard.

---

## 📦 Repository Structure

```plaintext
gpu-inference-marketplace/
├── backend/                  # FastAPI Coordinator & OpenAI Proxy
│   ├── app/
│   │   ├── api/              # Auth, Consumer, Provider, Models, Admin & OpenAI routers
│   │   ├── core/             # Config, SQLite DB engine, Security & JWT
│   │   ├── models/           # SQLAlchemy Relational Models (Users, Nodes, Ledgers)
│   │   ├── schemas/          # Pydantic Schemas & OpenAI specs
│   │   └── services/         # Smart Router, Billing Ledger, Tokenizer
│   └── tests/
│       └── test_e2e.py       # Automated End-to-End Marketplace Integration Test
├── worker/                   # Provider Worker Daemon CLI (nexus-worker)
│   └── nexus_worker/
│       ├── cli.py            # CLI entrypoint with Rich terminal styling
│       ├── hardware.py       # NVIDIA CUDA, Apple Metal & CPU hardware detector
│       ├── engine.py         # Ollama, vLLM & Emulation runtime bridge
│       └── client.py         # Outbound WebSocket uplink & streaming handler
├── frontend/                 # Vite + React + Tailwind Web Dashboard
│   └── src/
│       ├── components/       # Marketplace, Chat Playground, Consumer, Provider, Admin
│       ├── api.ts            # Client API & SSE Streaming parser
│       └── types.ts          # TypeScript domain definitions
├── docker-compose.yml        # Turnkey container orchestration
└── README.md
```

---

## 🛠️ Step-by-Step Local Setup & Execution Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ & npm

---

### Step 1: Start the Backend Coordinator

1. Navigate to the root directory and activate the virtual environment:
   ```bash
   # On Windows PowerShell:
   .\.venv\Scripts\Activate.ps1

   # On Linux/macOS:
   source .venv/bin/activate
   ```

2. Start the FastAPI coordinator:
   ```bash
   python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   - **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **OpenAI Endpoint**: `http://localhost:8000/v1/chat/completions`

---

### Step 2: Start the Web Dashboard

1. Open a new terminal tab and start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```
2. Open your browser at **[http://localhost:3000](http://localhost:3000)**.

---

### Step 3: Connect a GPU Provider Worker Node

1. In the web dashboard at `http://localhost:3000`:
   - Click **Connect / Login** and create an account (e.g. `provider@homelab.ai`).
   - Navigate to the **Provider Node** tab.
   - Enter a node name (e.g. `Rig-RTX4090`) and click **Add Node**.
   - Copy the generated terminal command containing your node token (`nx-node-...`).

2. In a new terminal tab, start the worker daemon:
   ```bash
   # Test node hardware and scan local engines:
   python worker/nexus_worker/cli.py info

   # Connect outbound to the network:
   python worker/nexus_worker/cli.py start --token <YOUR_NODE_TOKEN>
   ```

*(Note: If Ollama is running locally, the worker immediately discovers your local models. If Ollama is not installed, the worker automatically runs in test emulation mode, simulating a live high-performance node).*

---

### Step 4: Test Inference in the Browser Playground

1. Go to the **Playground** tab at `http://localhost:3000`.
2. Select your connected model (e.g., `llama3:8b` or `deepseek-r1:7b`).
3. Type a prompt (e.g., *"Explain decentralized AI in three sentences"*).
4. Watch the tokens stream in real time, with the **Telemetry HUD** displaying:
   - **tok/s Generation Speed**
   - **Latency (ms)**
   - **Total Tokens**
   - **Micro-Billing Cost ($)**

---

### Step 5: Test via the Official OpenAI Python SDK

1. Go to the **Consumer API** tab and click **Create Key** (or use the one created during onboarding).
2. Run this Python snippet:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="<YOUR_NX_API_KEY>"  # e.g., nx-live-...
)

response = client.chat.completions.create(
    model="llama3:8b",
    messages=[
        {"role": "system", "content": "You are a decentralized assistant."},
        {"role": "user", "content": "What is the benefit of a decentralized GPU network?"}
    ],
    stream=True
)

for chunk in response:
    print(chunk.choices[0].delta.content or "", end="", flush=True)
```

---

## 🧪 Automated End-to-End Verification

To verify the complete integration (user auth, wallet faucet, worker handshake, OpenAI streaming proxy, and financial settlement) with a single command:

```bash
python -u backend/tests/test_e2e.py
```

---

## 🔒 Security & Threat Model Summary

- **Provider Machine Isolation**: The worker daemon **never** runs untrusted binary code. It only relays structured JSON messages to local Ollama/vLLM HTTP endpoints.
- **Zero Inbound Port Exposure**: Workers initiate **outbound TLS WebSockets** only. No port forwarding is required on provider LANs.
- **Verifiable Prompt Tokens**: Coordinator independently calculates prompt token counts before job dispatch to prevent prompt-inflation billing fraud.
- **Credit Escrow Protection**: Minimum credits are pre-authorized in escrow before streaming commences, preventing drain attacks on provider nodes.
