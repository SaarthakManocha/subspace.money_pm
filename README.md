# Subspace.money Product Teardown: Engineering Prototypes

An interactive software engineering prototype developed as a core technical deliverable for the Subspace.money Product Internship Assignment (May 2026). This repository moves beyond abstract product concepts to deliver working, production-ready backend architectures and user interfaces built to solve structural friction loops identified within the live application.

## Architectural Overview

The code base implements a decoupled, full-stack architecture designed to demonstrate the technical feasibility and product mechanics of two high-leverage product iterations:

├── main.py          # FastAPI High-Performance Backend Core
├── dashboard.py     # Streamlit Visual Experience UI Layer
└── requirements.txt # System Dependency Manifest


### 1. The "Trust Shield" Interface Abstraction Layer
*   **The Problem:** The live app displays deep technical escrow breakdowns ("Locked Balance" vs "Unlocked Balance"), exposing complex financial mechanisms directly to consumers, which spikes user anxiety and customer support volumes.
*   **The Technical Fix:** `main.py` abstracts backend escrow buckets into a single, consolidated frontend data stream. The interface maps these balances into a reassuring visual progress paradigm ("Protected Balance"), re-framing security parameters from a restriction into a platform benefit.

### 2. The Instant Provisional AI Refund Engine
*   **The Problem:** Transaction failures and password mismatches currently face a 10-day Turnaround Time (TAT) refund policy, leading to critical buyer remorse and negative public sentiment loops.
*   **The Technical Fix:** Implements an automated dispute evaluation endpoint. When an API mismatch occurs, the engine programmatically audits the gateway logs, verifies the system failure, and instantly issues a provisional credit directly to the user's ledger. This balance can be immediately re-spent inside the Subspace ecosystem but is programmatically locked via a 48-hour cryptographic flag (`is_bank_withdrawable=False`) to isolate against friendly fraud during human backend reconciliation.

---

## Local Installation & Execution

Follow these steps to run the interactive full-stack simulation locally:

### 1. Clone the Repository
```bash
git clone [https://github.com/YOUR_USERNAME/subspace-product-prototype.git](https://github.com/YOUR_USERNAME/subspace-product-prototype.git)
cd subspace-product-prototype
```
### 2. Install Dependencies
Ensure you have Python 3.9+ installed, then execute:

```bash
pip install -r requirements.txt
```
### 3. Launch the FastAPI Backend Core
Start the high-performance backend processing engine via Uvicorn:

```bash
uvicorn main:app --reload --port 8000
```
The interactive Swagger API documentation will be available immediately at: http://127.0.0.1:8000/docs

### 4. Launch the Interactive Front-End Dashboard
In a parallel terminal window, ignite the front-end simulation dashboard:

```bash
streamlit run dashboard.py
```
The interactive visualization panel will open automatically inside your browser at: http://localhost:8501

### Core Engineering Frameworks Demonstrated

State Machine Management: Programmatically handles conditional transaction routing to prevent race conditions during wallet state updates.

Fintech Compliance Safety Loops: Demonstrates how to preserve structural corporate capital floats and manage ledger security without degrading consumer-facing design aesthetics.

Decoupled System Modeling: Built entirely using asynchronous patterns to match the requirements of highly scalable financial technology platforms processing massive daily transaction pipelines.

---
