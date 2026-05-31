"""
dashboard.py — Streamlit Visual Interactive UI for Subspace.money Prototypes
=============================================================================

Renders two core experiences:

1. **Trust Shield Dashboard**
   Consolidated wallet view with a visual progress bar for escrowed
   (protected) funds.  Replaces confusing escrow jargon with a
   reassuring "Protected Balance" state.

2. **Instant Dispute Simulation**
   One-click button that creates a failed checkout, disputes it, and
   visually demonstrates the provisional credit appearing in the wallet
   in real time.

Run (after starting the FastAPI backend on port 8000):
    streamlit run dashboard.py
"""

from __future__ import annotations

import time
from datetime import datetime

import requests
import streamlit as st

# ─────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────

API_BASE = "http://localhost:8000"

# ─────────────────────────────────────────────────────────────────────
# Page Config & Styling
# ─────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Subspace.money — Trust Shield Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom CSS for a polished, branded look.
st.markdown(
    """
    <style>
    /* ── Global ───────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* ── Metric cards ─────────────────────────────────────────── */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 20px 24px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.25);
    }
    div[data-testid="stMetric"] label {
        color: #a0aec0 !important;
        font-weight: 500;
        font-size: 0.85rem !important;
        letter-spacing: 0.02em;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #e2e8f0 !important;
        font-weight: 700;
        font-size: 1.75rem !important;
    }

    /* ── Progress bar override ────────────────────────────────── */
    div[data-testid="stProgress"] > div > div {
        background-color: #22c55e !important;
        border-radius: 8px;
    }

    /* ── Sidebar polish ───────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }

    /* ── Success / info banners ───────────────────────────────── */
    div[data-testid="stAlert"] {
        border-radius: 12px;
    }

    /* ── Custom shield banner ─────────────────────────────────── */
    .shield-banner {
        background: linear-gradient(135deg, #065f46 0%, #064e3b 100%);
        border: 1px solid #10b981;
        border-radius: 16px;
        padding: 20px 28px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .shield-banner .icon { font-size: 2rem; }
    .shield-banner .text {
        color: #d1fae5;
        font-size: 1rem;
        font-weight: 500;
    }

    /* ── Credit card component ────────────────────────────────── */
    .credit-card {
        background: linear-gradient(135deg, #312e81 0%, #4c1d95 100%);
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 12px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .credit-card h4 {
        color: #c4b5fd;
        margin: 0 0 6px 0;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .credit-card .amount {
        color: #f5f3ff;
        font-size: 1.5rem;
        font-weight: 700;
    }
    .credit-card .meta {
        color: #a78bfa;
        font-size: 0.8rem;
        margin-top: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────
# Helper — API Calls
# ─────────────────────────────────────────────────────────────────────

def api_get(path: str) -> dict | None:
    """GET request to the FastAPI backend; returns JSON or None on error."""
    try:
        resp = requests.get(f"{API_BASE}{path}", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        st.error(f"⚠️ Backend unreachable — is `uvicorn main:app` running on port 8000?  ({exc})")
        return None


def api_post(path: str, payload: dict) -> dict | None:
    """POST request to the FastAPI backend; returns JSON or None on error."""
    try:
        resp = requests.post(f"{API_BASE}{path}", json=payload, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as exc:
        # Surface 4xx detail messages from FastAPI.
        try:
            detail = exc.response.json().get("detail", str(exc))
        except Exception:
            detail = str(exc)
        st.warning(f"⚠️ {detail}")
        return None
    except requests.RequestException as exc:
        st.error(f"⚠️ Backend unreachable — is `uvicorn main:app` running on port 8000?  ({exc})")
        return None


# ─────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🛡️ Subspace.money")
    st.markdown("##### Trust Shield Prototype")
    st.divider()
    st.markdown(
        "This dashboard demonstrates two product features:\n\n"
        "1. **Trust Shield** — consolidated ledger with protected-balance UX.\n"
        "2. **Instant AI Refund** — one-click provisional credit engine."
    )
    st.divider()
    st.caption("Backend: FastAPI · Frontend: Streamlit")
    st.caption("© 2025 Subspace.money Teardown Prototype")


# ─────────────────────────────────────────────────────────────────────
# Main Layout
# ─────────────────────────────────────────────────────────────────────

st.markdown("# 🛡️ Trust Shield Dashboard")
st.markdown("*Your money, always protected — no jargon, just clarity.*")
st.markdown("---")

# ── Fetch wallet data ────────────────────────────────────────────────
wallet = api_get("/wallet/balance")

if wallet:
    # ── Trust Shield Status Banner ───────────────────────────────────
    st.markdown(
        f"""
        <div class="shield-banner">
            <span class="icon">🛡️</span>
            <span class="text">{wallet["trust_shield_status"]}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Key Metrics Row ──────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Balance",
            value=f"₹{wallet['total_balance']:,.2f}",
        )
    with col2:
        st.metric(
            label="Available to Withdraw",
            value=f"₹{wallet['available_to_withdraw']:,.2f}",
        )
    with col3:
        st.metric(
            label="Protected (Cashback Escrow)",
            value=f"₹{wallet['protected_balance']:,.2f}",
        )
    with col4:
        st.metric(
            label="Provisional Credits",
            value=f"₹{wallet['provisional_total']:,.2f}",
        )

    st.markdown("")

    # ── Protected Balance Progress Bar ───────────────────────────────
    st.markdown("### 🔒 Cashback Protection Progress")
    st.markdown(
        "Your cashback rewards are being securely held until the merchant "
        "settlement window closes.  Once verified, they'll move to your "
        "withdrawable balance automatically."
    )

    progress_value = wallet["protected_balance_progress_pct"] / 100
    st.progress(
        progress_value,
        text=f"Escrow release: {wallet['protected_balance_progress_pct']:.0f}% complete",
    )

    st.markdown("")

    # ── Provisional Credits Detail ───────────────────────────────────
    if wallet["provisional_credits"]:
        st.markdown("### ⏳ Active Provisional Credits")
        st.markdown(
            "These are instant refund credits issued by the AI dispute engine.  "
            "They're **spendable now** within Subspace but cannot be withdrawn "
            "to your bank until the security lock expires."
        )

        for pc in wallet["provisional_credits"]:
            lock_status = "🔓 Unlocked" if pc["is_bank_withdrawable"] else "🔒 Bank-Locked"
            remaining = pc["time_remaining_hours"]
            hours_display = f"{remaining:.1f}h remaining" if remaining > 0 else "Ready to withdraw"

            st.markdown(
                f"""
                <div class="credit-card">
                    <h4>{pc["credit_id"]} · {lock_status}</h4>
                    <div class="amount">₹{pc["amount"]:,.2f}</div>
                    <div class="meta">
                        ⏱️ {hours_display} · Unlocks {pc["unlocks_at"][:16].replace("T", " ")} UTC<br/>
                        🔐 Lock hash: <code>{pc["cryptographic_lock_hash"][:24]}…</code>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("✅ No provisional credits — all balances are fully settled.")


# ─────────────────────────────────────────────────────────────────────
# Dispute Simulation Section
# ─────────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("## ⚡ Instant AI Refund — Live Simulation")
st.markdown(
    "Click the button below to run a **full end-to-end dispute cycle**:\n\n"
    "1. A checkout is created with a simulated gateway failure.\n"
    "2. The AI audit engine scans the transaction logs.\n"
    "3. A provisional credit is issued instantly to your wallet.\n"
    "4. The dashboard refreshes to show the updated balance."
)

col_btn, col_amount = st.columns([1, 2])

with col_amount:
    dispute_amount = st.number_input(
        "Simulated transaction amount (₹)",
        min_value=100.0,
        max_value=50000.0,
        value=1499.0,
        step=100.0,
    )

with col_btn:
    st.markdown("")  # vertical spacer
    run_simulation = st.button(
        "🚀 Trigger Dispute Simulation",
        type="primary",
        use_container_width=True,
    )

if run_simulation:
    with st.status("Running dispute simulation...", expanded=True) as status:

        # ── Step 1: Create a failed checkout ─────────────────────────
        st.write("📤 **Step 1** — Creating checkout with simulated failure…")
        checkout = api_post("/checkout/direct-route", {
            "amount": dispute_amount,
            "simulate_failure": True,
        })

        if not checkout:
            status.update(label="Simulation failed", state="error")
            st.stop()

        txn_id = checkout["transaction_id"]
        st.write(f"  ↳ Transaction `{txn_id}` — status: **{checkout['status']}**")
        st.write(f"  ↳ Gateway error: `{checkout.get('gateway_error', 'N/A')}`")
        time.sleep(0.6)  # brief pause for visual effect

        # ── Step 2: Trigger the AI dispute engine ────────────────────
        st.write("🤖 **Step 2** — AI audit engine scanning logs…")
        time.sleep(0.8)

        dispute = api_post("/disputes/provisional-refund", {
            "transaction_id": txn_id,
        })

        if not dispute:
            status.update(label="Simulation failed", state="error")
            st.stop()

        st.write(f"  ↳ Audit result: **{dispute['ai_audit_result']}**")
        st.write(f"  ↳ Error detected: `{dispute.get('gateway_error_detected', 'none')}`")
        time.sleep(0.5)

        # ── Step 3: Show provisional credit ──────────────────────────
        if dispute.get("provisional_credit"):
            pc = dispute["provisional_credit"]
            st.write("💸 **Step 3** — Provisional credit issued!")
            st.write(f"  ↳ Credit ID: `{pc['credit_id']}`")
            st.write(f"  ↳ Amount: **₹{pc['amount']:,.2f}**")
            st.write(f"  ↳ Bank withdrawable: `{pc['is_bank_withdrawable']}`")
            st.write(f"  ↳ Unlocks at: `{pc['unlocks_at'][:16]}` UTC")
        else:
            st.write("ℹ️ No provisional credit issued (manual review path).")

        status.update(label="✅ Simulation complete!", state="complete")

    # ── Show the backend message ─────────────────────────────────────
    st.success(dispute["message"])

    # ── Audit log details (expandable) ───────────────────────────────
    with st.expander("🔍 View Full AI Audit Log Entry"):
        st.json(dispute["audit_log_entry"])

    # ── Prompt user to see updated balance ───────────────────────────
    st.info("🔄 **Refresh the page** (Ctrl+R) to see the updated Trust Shield balances above.")


# ─────────────────────────────────────────────────────────────────────
# Direct Checkout Demo (Sidebar-Expandable)
# ─────────────────────────────────────────────────────────────────────

st.markdown("---")

with st.expander("🧪 Manual Direct-Route Checkout Demo"):
    st.markdown(
        "Test the **direct-route checkout** endpoint independently. "
        "Toggle *Simulate Failure* to create a failed transaction you "
        "can later dispute above."
    )

    mc1, mc2 = st.columns(2)
    with mc1:
        manual_amount = st.number_input("Amount (₹)", min_value=1.0, value=999.0, key="manual_amt")
    with mc2:
        sim_fail = st.checkbox("Simulate Failure", value=False)

    if st.button("Submit Checkout", key="manual_checkout"):
        result = api_post("/checkout/direct-route", {
            "amount": manual_amount,
            "simulate_failure": sim_fail,
        })
        if result:
            st.json(result)


# ─────────────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────────────

st.markdown("---")
st.caption(
    "Built as a working prototype for the Subspace.money product teardown assignment. "
    "Not intended for production financial use."
)
