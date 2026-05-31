# 🛡️ Subspace.money — Trust Shield, AI Refund & Subscription Audit Prototype

> Working code prototypes for the Subspace.money product management teardown assignment.

An interactive software engineering prototype developed as a core technical deliverable for the Subspace.money Product Internship Assignment (May 2026). This repository moves beyond abstract product concepts to deliver working, production-ready backend architectures and user interfaces built to solve structural friction loops identified within the live application.

This repository implements **three core product features** identified in the teardown report:

| Feature | What It Solves | Implementation |
|---------|---------------|----------------|
| **Trust Shield Ledger** | Users see confusing "locked" / "escrowed" balances and panic | Consolidated wallet view with clear "Available to Withdraw" + visual progress bar for protected funds |
| **Instant Provisional AI Refund** | Dispute resolution takes days; users lose trust | AI-audited gateway log scan → instant 48-hour bank-locked provisional credit |
| **AI Subscription Audit** | Users overpay retail for subscriptions they could split | Financial footprint scanner detecting subs + one-click migration to Subspace group pools |

---

## Architecture

```
┌──────────────────────────┐         ┌──────────────────────────┐
│   dashboard.py           │  HTTP   │   main.py                │
│   (Streamlit Frontend)   │ ◄─────► │   (FastAPI Backend)      │
│                          │         │                          │
│  • Trust Shield View     │         │  POST /checkout/direct   │
│  • Dispute Simulation    │         │  POST /disputes/refund   │
│  • Subscription Audit    │         │  POST /subs/audit        │
│  • Real-time UI Updates  │         │  POST /subs/optimize     │
│                          │         │  GET  /wallet/balance    │
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

### `POST /subscriptions/audit`
AI-powered scan of the user's financial footprint (bank statements, UPI mandates, SMS alerts). Returns detected subscriptions with retail vs. Subspace split pricing and savings calculations.

```json
{}
```
*No payload required — the AI scans the user's linked financial data automatically.*

### `POST /subscriptions/optimize`
Routes a detected subscription into a Subspace group-split pool, instantly reducing the user's monthly cost.

```json
{
  "sub_id": "SUB-NETFLIX-001"
}
```

---

## Key Design Decisions

1. **`is_bank_withdrawable=False`** — Provisional credits are spendable within Subspace instantly, but bank withdrawal is blocked for 48 hours. This protects against fraud while keeping the user experience instant.

2. **Cryptographic lock hash** — Each provisional credit includes a SHA-256 commitment hash binding the credit parameters. In production, this would feed into a Merkle proof for banking partner reconciliation.

3. **Progress abstraction** — Instead of showing raw escrow states ("T+3 settlement pending"), the Trust Shield UI shows a progress bar with human-friendly language ("62% — your cashback is being verified").

4. **Subscription pool routing** — The optimize endpoint simulates cancelling a user's retail UPI autopay mandate and enrolling them into a Subspace-managed family/group plan at a fraction of the cost.

---

## Tech Stack

- **Backend**: FastAPI + Pydantic (type-safe, auto-documented)
- **Frontend**: Streamlit (rapid interactive prototyping)
- **Language**: Python 3.10+

---

*Built as a prototype for the Subspace.money PM internship teardown assignment.*
