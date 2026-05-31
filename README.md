# Subspace.money — Trust Shield & Instant AI Refund Prototype

> Working code prototypes for the Subspace.money product management teardown assignment.

An interactive software engineering prototype developed as a core technical deliverable for the Subspace.money Product Internship Assignment (May 2026). This repository moves beyond abstract product concepts to deliver working, production-ready backend architectures and user interfaces built to solve structural friction loops identified within the live application.

This repository implements **two core product features** identified in the teardown report:

| Feature | What It Solves | Implementation |
|---------|---------------|----------------|
| **Trust Shield Ledger** | Users see confusing "locked" / "escrowed" balances and panic | Consolidated wallet view with clear "Available to Withdraw" + visual progress bar for protected funds |
| **Instant Provisional AI Refund** | Dispute resolution takes days; users lose trust | AI-audited gateway log scan → instant 48-hour bank-locked provisional credit |

---

## Architecture

```
┌──────────────────────────┐         ┌──────────────────────────┐
│   dashboard.py           │  HTTP   │   main.py                │
│   (Streamlit Frontend)   │ ◄─────► │   (FastAPI Backend)      │
│                          │         │                          │
│  • Trust Shield View     │         │  POST /checkout/direct   │
│  • Dispute Simulation    │         │  POST /disputes/refund   │
│  • Real-time UI Updates  │         │  GET  /wallet/balance    │
└──────────────────────────┘         └──────────────────────────┘
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Backend (Terminal 1)

```bash
uvicorn main:app --reload --port 8000
```

The API docs are available at [http://localhost:8000/docs](http://localhost:8000/docs).

### 3. Start the Dashboard (Terminal 2)

```bash
streamlit run dashboard.py
```

The dashboard opens at [http://localhost:8501](http://localhost:8501).

---

## API Endpoints

### `POST /checkout/direct-route`
Bypasses manual wallet funding — simulates a direct UPI Autopay contextual deep-link checkout.

```json
{
  "amount": 1499.0,
  "simulate_failure": true
}
```

### `POST /disputes/provisional-refund`
Triggers the AI audit engine on a failed transaction and issues an instant provisional credit with a 48-hour bank lock.

```json
{
  "transaction_id": "TXN-XXXXXXXXXXXX"
}
```

### `GET /wallet/balance`
Returns the Trust Shield consolidated ledger — a single view with "Available to Withdraw", "Protected Balance" (with progress), and active provisional credits.

---

## Key Design Decisions

1. **`is_bank_withdrawable=False`** — Provisional credits are spendable within Subspace instantly, but bank withdrawal is blocked for 48 hours. This protects against fraud while keeping the user experience instant.

2. **Cryptographic lock hash** — Each provisional credit includes a SHA-256 commitment hash binding the credit parameters. In production, this would feed into a Merkle proof for banking partner reconciliation.

3. **Progress abstraction** — Instead of showing raw escrow states ("T+3 settlement pending"), the Trust Shield UI shows a progress bar with human-friendly language ("62% — your cashback is being verified").

---

## Tech Stack

- **Backend**: FastAPI + Pydantic (type-safe, auto-documented)
- **Frontend**: Streamlit (rapid interactive prototyping)
- **Language**: Python 3.10+

---

*Built as a prototype for the Subspace.money PM internship teardown assignment.*
