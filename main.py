"""
main.py — FastAPI Backend Engine for Subspace.money Feature Prototypes
======================================================================

Implements three core product features from the Subspace teardown report:

1. **Trust Shield Ledger Layer**
   Abstracts complex locked/unlocked escrow balances into a single,
   user-friendly consolidated wallet view with clear "Available to Withdraw"
   and "Protected Balance" states.

2. **Instant Provisional AI Refund Engine**
   Automates dispute resolution by scanning transactional logs for gateway
   errors and issuing 48-hour cryptographically bank-locked wallet credits
   that are spendable but not withdrawable until the lock window expires.

3. **One-Click AI Subscription Audit**
   Parses a user's financial footprint to detect active retail subscriptions,
   calculates potential savings via Subspace group-split pooling, and lets
   users migrate subscriptions into optimised pools with a single click.

Run:
    uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import hashlib
import random
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ─────────────────────────────────────────────────────────────────────
# App Initialisation
# ─────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Subspace.money — Trust Shield, AI Refund & Subscription Audit",
    description=(
        "Working prototype backend powering the Trust Shield consolidated "
        "ledger, the Instant Provisional AI Refund mechanism, and the "
        "One-Click AI Subscription Audit tool."
    ),
    version="2.0.0",
)

# Allow the Streamlit frontend (default port 8501) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────
# In-Memory Database (simulates persistent storage)
# ─────────────────────────────────────────────────────────────────────

# Single-user demo wallet.  In production this would be per-user rows
# in a relational database behind an ORM.

_wallet: dict = {
    "user_id": "demo_user_001",
    "available_balance": 5000.00,       # ₹ — freely withdrawable
    "escrowed_balance": 2000.00,        # ₹ — locked in active cashback escrows
    "provisional_credits": [],          # list[ProvisionalCredit]  — 48h locked
}

# Stores every checkout transaction so the dispute engine can audit them.
_transactions: dict[str, dict] = {}

# Global log of AI audit events for transparency.
_audit_log: list[dict] = []

# ── Mock Subscription Database ───────────────────────────────────────
# Simulates subscriptions detected from a user's bank/SMS financial
# footprint.  Each entry represents a real subscription the user is
# paying full retail price for that *could* be split via Subspace.

_detected_subscriptions: list[dict] = [
    {
        "sub_id": "SUB-NETFLIX-001",
        "service_name": "Netflix Premium",
        "category": "Streaming",
        "icon_emoji": "🎬",
        "retail_price": 649.00,
        "subspace_split_price": 163.00,
        "billing_cycle": "monthly",
        "detected_via": "UPI autopay mandate",
        "is_optimized": False,
    },
    {
        "sub_id": "SUB-YTPREM-002",
        "service_name": "YouTube Premium",
        "category": "Streaming",
        "icon_emoji": "▶️",
        "retail_price": 149.00,
        "subspace_split_price": 53.00,
        "billing_cycle": "monthly",
        "detected_via": "bank statement pattern",
        "is_optimized": False,
    },
    {
        "sub_id": "SUB-SPOTIFY-003",
        "service_name": "Spotify Premium",
        "category": "Music",
        "icon_emoji": "🎵",
        "retail_price": 119.00,
        "subspace_split_price": 35.00,
        "billing_cycle": "monthly",
        "detected_via": "SMS transaction alert",
        "is_optimized": False,
    },
    {
        "sub_id": "SUB-ICLOUD-004",
        "service_name": "iCloud+ 200GB",
        "category": "Cloud Storage",
        "icon_emoji": "☁️",
        "retail_price": 219.00,
        "subspace_split_price": 75.00,
        "billing_cycle": "monthly",
        "detected_via": "UPI autopay mandate",
        "is_optimized": False,
    },
    {
        "sub_id": "SUB-LINKEDIN-005",
        "service_name": "LinkedIn Premium",
        "category": "Professional",
        "icon_emoji": "💼",
        "retail_price": 1999.00,
        "subspace_split_price": 514.00,
        "billing_cycle": "monthly",
        "detected_via": "bank statement pattern",
        "is_optimized": False,
    },
]


# ─────────────────────────────────────────────────────────────────────
# Enums & Pydantic Schemas
# ─────────────────────────────────────────────────────────────────────

class TransactionStatus(str, Enum):
    """Lifecycle states a checkout transaction can pass through."""
    INITIATED = "initiated"
    SUCCESS = "success"
    FAILED = "failed"
    DISPUTED = "disputed"
    REFUNDED = "refunded"


class GatewayErrorType(str, Enum):
    """Known payment-gateway error classes the AI auditor can detect."""
    TIMEOUT = "gateway_timeout"
    DUPLICATE_DEBIT = "duplicate_debit"
    PARTIAL_CAPTURE = "partial_capture"
    NONE = "none"


# ── Request Bodies ───────────────────────────────────────────────────

class CheckoutRequest(BaseModel):
    """Payload for the direct-route checkout endpoint."""
    amount: float = Field(..., gt=0, description="Transaction amount in ₹")
    merchant_id: str = Field(
        default="merchant_subspace_001",
        description="Merchant receiving the payment",
    )
    upi_vpa: str = Field(
        default="user@okbank",
        description="User's UPI Virtual Payment Address",
    )
    simulate_failure: bool = Field(
        default=False,
        description="If True, the checkout will simulate a gateway failure "
                    "so the dispute flow can be demonstrated.",
    )


class DisputeRequest(BaseModel):
    """Payload for triggering the AI provisional-refund engine."""
    transaction_id: str = Field(
        ..., description="The checkout transaction ID to dispute"
    )


# ── Response Bodies ──────────────────────────────────────────────────

class CheckoutResponse(BaseModel):
    transaction_id: str
    status: TransactionStatus
    amount: float
    merchant_id: str
    upi_deeplink: str
    gateway_error: Optional[GatewayErrorType] = None
    timestamp: str


class ProvisionalCreditDetail(BaseModel):
    """A single 48-hour bank-locked provisional credit."""
    credit_id: str
    amount: float
    is_bank_withdrawable: bool          # always False during the lock window
    issued_at: str
    unlocks_at: str
    time_remaining_hours: float
    cryptographic_lock_hash: str        # SHA-256 commitment of credit params


class WalletBalanceResponse(BaseModel):
    """
    The **Trust Shield** consolidated ledger view.

    Instead of exposing raw escrow accounting, this presents a single
    reassuring interface:
      • available_to_withdraw  — cash the user can move to their bank
      • protected_balance      — cashback escrows progressing toward release
      • provisional_credits    — dispute refunds locked for 48 h
      • total_balance          — the sum the user can *spend* within Subspace
    """
    user_id: str
    available_to_withdraw: float
    protected_balance: float
    protected_balance_progress_pct: float   # 0-100 visual progress
    provisional_credits: list[ProvisionalCreditDetail]
    provisional_total: float
    total_balance: float
    trust_shield_status: str                # e.g. "All Funds Protected ✓"
    last_updated: str


class DisputeResponse(BaseModel):
    transaction_id: str
    ai_audit_result: str
    gateway_error_detected: Optional[GatewayErrorType]
    provisional_credit: Optional[ProvisionalCreditDetail]
    audit_log_entry: dict
    message: str


# ── Subscription Audit Schemas ───────────────────────────────────────

class DetectedSubscription(BaseModel):
    """A single subscription detected from the user's financial footprint."""
    sub_id: str
    service_name: str
    category: str
    icon_emoji: str
    retail_price: float                 # what the user currently pays
    subspace_split_price: float         # what they'd pay via Subspace pool
    monthly_savings: float              # retail − split
    savings_pct: float                  # percentage saved
    billing_cycle: str
    detected_via: str                   # how the AI found this subscription
    is_optimized: bool                  # already routed through Subspace?


class SubscriptionAuditResponse(BaseModel):
    """Result of the AI subscription financial footprint scan."""
    user_id: str
    total_retail_spend: float           # current monthly total
    total_optimized_spend: float        # projected total via Subspace
    total_monthly_savings: float
    total_annual_savings: float
    subscriptions: list[DetectedSubscription]
    scan_summary: str
    scanned_at: str


class OptimizeRequest(BaseModel):
    """Payload to migrate a subscription into a Subspace pool."""
    sub_id: str = Field(..., description="ID of the subscription to optimize")


class OptimizeResponse(BaseModel):
    """Confirmation of a successful subscription optimization."""
    sub_id: str
    service_name: str
    previous_price: float
    new_price: float
    monthly_savings: float
    pool_id: str                        # the Subspace pool it was routed to
    message: str


# ─────────────────────────────────────────────────────────────────────
# Utility Helpers
# ─────────────────────────────────────────────────────────────────────

def _now() -> datetime:
    """Current UTC time."""
    return datetime.now(timezone.utc)


def _generate_lock_hash(credit_id: str, amount: float, unlocks_at: str) -> str:
    """
    Produce a SHA-256 commitment hash that cryptographically binds the
    credit parameters.  In production this would be part of a Merkle
    proof submitted to the banking partner.
    """
    payload = f"{credit_id}:{amount}:{unlocks_at}:{secrets.token_hex(8)}"
    return hashlib.sha256(payload.encode()).hexdigest()


def _simulate_gateway_error() -> GatewayErrorType:
    """Pick a random gateway error for demo purposes."""
    return random.choice([
        GatewayErrorType.TIMEOUT,
        GatewayErrorType.DUPLICATE_DEBIT,
        GatewayErrorType.PARTIAL_CAPTURE,
    ])


# ─────────────────────────────────────────────────────────────────────
# AI Audit Engine (simulated)
# ─────────────────────────────────────────────────────────────────────

def _run_ai_audit(txn: dict) -> tuple[bool, GatewayErrorType, str]:
    """
    Simulates the AI-powered transactional log audit.

    In production this module would:
      1. Pull raw gateway logs (Razorpay / Juspay webhook payloads).
      2. Cross-reference the bank settlement file.
      3. Apply heuristic + ML classification to identify error class.
      4. Return a confidence-scored verdict.

    For this prototype we deterministically detect gateway errors
    recorded during checkout simulation.

    Returns:
        (is_eligible, error_type, audit_summary)
    """
    gateway_error = txn.get("gateway_error", GatewayErrorType.NONE)

    if gateway_error != GatewayErrorType.NONE:
        summary = (
            f"AI Audit — ELIGIBLE: Detected [{gateway_error.value}] on "
            f"txn {txn['transaction_id']}.  Amount ₹{txn['amount']:.2f} "
            f"qualifies for instant provisional refund."
        )
        return True, gateway_error, summary

    # No error detected — manual review path.
    summary = (
        f"AI Audit — NOT ELIGIBLE: No gateway anomaly found for "
        f"txn {txn['transaction_id']}.  Escalating to manual review."
    )
    return False, GatewayErrorType.NONE, summary


# ─────────────────────────────────────────────────────────────────────
# Endpoint 1 — Direct-Route Checkout (UPI Autopay Deep-Link)
# ─────────────────────────────────────────────────────────────────────

@app.post(
    "/checkout/direct-route",
    response_model=CheckoutResponse,
    tags=["Checkout"],
    summary="Bypass manual wallet funding with a direct UPI Autopay deep-link",
)
async def checkout_direct_route(payload: CheckoutRequest) -> CheckoutResponse:
    """
    **Direct-Route Checkout**

    Eliminates the friction of manually pre-loading the Subspace wallet.
    Instead, the system generates a contextual UPI Autopay deep-link that
    lets the user pay the merchant directly — Subspace captures the
    cashback opportunity in the background.

    If `simulate_failure=True`, the transaction records a gateway error
    so you can later trigger the dispute flow.
    """
    txn_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
    now = _now()

    # Determine success or simulated failure.
    if payload.simulate_failure:
        status = TransactionStatus.FAILED
        gateway_error = _simulate_gateway_error()
    else:
        status = TransactionStatus.SUCCESS
        gateway_error = GatewayErrorType.NONE

    # Construct a UPI deep-link (demo format).
    upi_deeplink = (
        f"upi://pay?pa={payload.merchant_id}@upi"
        f"&pn=Subspace%20Merchant"
        f"&am={payload.amount}"
        f"&tn={txn_id}"
        f"&cu=INR"
    )

    # Persist the transaction.
    txn_record = {
        "transaction_id": txn_id,
        "amount": payload.amount,
        "merchant_id": payload.merchant_id,
        "upi_vpa": payload.upi_vpa,
        "status": status.value,
        "gateway_error": gateway_error,
        "upi_deeplink": upi_deeplink,
        "created_at": now.isoformat(),
    }
    _transactions[txn_id] = txn_record

    # If successful, simulate cashback being escrowed.
    if status == TransactionStatus.SUCCESS:
        cashback = round(payload.amount * 0.05, 2)  # 5 % cashback demo
        _wallet["escrowed_balance"] += cashback

    return CheckoutResponse(
        transaction_id=txn_id,
        status=status,
        amount=payload.amount,
        merchant_id=payload.merchant_id,
        upi_deeplink=upi_deeplink,
        gateway_error=gateway_error if gateway_error != GatewayErrorType.NONE else None,
        timestamp=now.isoformat(),
    )


# ─────────────────────────────────────────────────────────────────────
# Endpoint 2 — Instant Provisional AI Refund
# ─────────────────────────────────────────────────────────────────────

@app.post(
    "/disputes/provisional-refund",
    response_model=DisputeResponse,
    tags=["Disputes"],
    summary="AI-audited instant provisional refund with 48-hour bank lock",
)
async def provisional_refund(payload: DisputeRequest) -> DisputeResponse:
    """
    **Instant Provisional AI Refund Engine**

    1. Looks up the disputed transaction.
    2. Runs the AI audit engine against the gateway logs.
    3. If a known error pattern is detected, instantly issues a
       **provisional credit** to the user's wallet.
    4. The credit is spendable within Subspace but is flagged
       `is_bank_withdrawable=False` for a 48-hour time-lock window.
    5. After 48 hours (simulated), the lock lifts and the credit
       becomes fully withdrawable.
    """
    # ── Step 1: Validate the transaction exists ──────────────────────
    txn = _transactions.get(payload.transaction_id)
    if not txn:
        raise HTTPException(
            status_code=404,
            detail=f"Transaction {payload.transaction_id} not found.",
        )

    # Prevent duplicate disputes.
    if txn["status"] in (TransactionStatus.DISPUTED.value, TransactionStatus.REFUNDED.value):
        raise HTTPException(
            status_code=409,
            detail=f"Transaction {payload.transaction_id} has already been "
                   f"disputed or refunded.",
        )

    # ── Step 2: Run the AI audit ─────────────────────────────────────
    is_eligible, error_type, audit_summary = _run_ai_audit(txn)

    audit_entry = {
        "audit_id": f"AUD-{uuid.uuid4().hex[:8].upper()}",
        "transaction_id": payload.transaction_id,
        "result": "eligible" if is_eligible else "not_eligible",
        "error_type": error_type.value,
        "summary": audit_summary,
        "audited_at": _now().isoformat(),
    }
    _audit_log.append(audit_entry)

    # ── Step 3: Issue provisional credit (if eligible) ───────────────
    if not is_eligible:
        # Mark as disputed but no auto-refund.
        txn["status"] = TransactionStatus.DISPUTED.value
        return DisputeResponse(
            transaction_id=payload.transaction_id,
            ai_audit_result="not_eligible",
            gateway_error_detected=None,
            provisional_credit=None,
            audit_log_entry=audit_entry,
            message=(
                "No gateway anomaly detected.  Your dispute has been "
                "escalated to manual review.  A support agent will "
                "respond within 24 hours."
            ),
        )

    # Create the 48-hour bank-locked provisional credit.
    now = _now()
    unlock_time = now + timedelta(hours=48)
    credit_id = f"PC-{uuid.uuid4().hex[:10].upper()}"
    lock_hash = _generate_lock_hash(credit_id, txn["amount"], unlock_time.isoformat())

    provisional = {
        "credit_id": credit_id,
        "amount": txn["amount"],
        "is_bank_withdrawable": False,       # ← 48-hour bank lock
        "issued_at": now.isoformat(),
        "unlocks_at": unlock_time.isoformat(),
        "cryptographic_lock_hash": lock_hash,
    }

    # Write to the wallet.
    _wallet["provisional_credits"].append(provisional)
    _wallet["available_balance"] += txn["amount"]   # spendable immediately

    # Update the transaction status.
    txn["status"] = TransactionStatus.REFUNDED.value

    # Build the response detail.
    remaining_hours = (unlock_time - now).total_seconds() / 3600
    credit_detail = ProvisionalCreditDetail(
        credit_id=credit_id,
        amount=txn["amount"],
        is_bank_withdrawable=False,
        issued_at=now.isoformat(),
        unlocks_at=unlock_time.isoformat(),
        time_remaining_hours=round(remaining_hours, 2),
        cryptographic_lock_hash=lock_hash,
    )

    return DisputeResponse(
        transaction_id=payload.transaction_id,
        ai_audit_result="eligible",
        gateway_error_detected=error_type,
        provisional_credit=credit_detail,
        audit_log_entry=audit_entry,
        message=(
            f"Provisional credit of ₹{txn['amount']:.2f} issued instantly. "
            f"Funds are spendable now but bank withdrawal unlocks at "
            f"{unlock_time.strftime('%d %b %Y, %H:%M UTC')}."
        ),
    )


# ─────────────────────────────────────────────────────────────────────
# Endpoint 3 — Trust Shield Consolidated Wallet Balance
# ─────────────────────────────────────────────────────────────────────

@app.get(
    "/wallet/balance",
    response_model=WalletBalanceResponse,
    tags=["Wallet"],
    summary="Trust Shield consolidated ledger view",
)
async def wallet_balance() -> WalletBalanceResponse:
    """
    **Trust Shield Ledger Layer**

    Returns a *single, human-friendly* wallet view that abstracts away
    raw escrow accounting:

    | Field                    | Meaning                                  |
    |--------------------------|------------------------------------------|
    | available_to_withdraw    | Cash the user can send to their bank     |
    | protected_balance        | Cashback escrows progressing to release   |
    | provisional_credits      | Dispute refunds under 48 h bank lock     |
    | total_balance            | Everything the user can spend in-app     |

    The `protected_balance_progress_pct` value drives the Trust Shield
    progress bar in the frontend — it represents how close the next
    escrow tranche is to unlocking.
    """
    now = _now()

    # ── Compute provisional credit details ───────────────────────────
    credit_details: list[ProvisionalCreditDetail] = []
    provisional_total = 0.0

    for pc in _wallet["provisional_credits"]:
        unlock_dt = datetime.fromisoformat(pc["unlocks_at"])
        remaining = max((unlock_dt - now).total_seconds() / 3600, 0)

        # If the lock has expired, flip the flag (simulates cron job).
        is_locked = remaining > 0

        credit_details.append(ProvisionalCreditDetail(
            credit_id=pc["credit_id"],
            amount=pc["amount"],
            is_bank_withdrawable=not is_locked,
            issued_at=pc["issued_at"],
            unlocks_at=pc["unlocks_at"],
            time_remaining_hours=round(remaining, 2),
            cryptographic_lock_hash=pc["cryptographic_lock_hash"],
        ))
        if is_locked:
            provisional_total += pc["amount"]

    # ── Protected balance progress (simulated escrow release %) ──────
    # In production, this would be calculated from actual escrow
    # milestones (e.g., 7-day merchant settlement windows).
    # Here we simulate a slowly progressing escrow at 62 %.
    escrow_progress = 62.0  # percent toward next cashback release

    # ── Total spendable balance ──────────────────────────────────────
    total = (
        _wallet["available_balance"]
        + _wallet["escrowed_balance"]
        + provisional_total
    )

    # ── Trust Shield status label ────────────────────────────────────
    if provisional_total > 0:
        shield_status = "Active — Provisional Credits Under Review"
    elif _wallet["escrowed_balance"] > 0:
        shield_status = "All Funds Protected ✓"
    else:
        shield_status = "No Active Protections"

    return WalletBalanceResponse(
        user_id=_wallet["user_id"],
        available_to_withdraw=_wallet["available_balance"],
        protected_balance=_wallet["escrowed_balance"],
        protected_balance_progress_pct=escrow_progress,
        provisional_credits=credit_details,
        provisional_total=provisional_total,
        total_balance=round(total, 2),
        trust_shield_status=shield_status,
        last_updated=now.isoformat(),
    )


# ─────────────────────────────────────────────────────────────────────
# Endpoint 4 — AI Subscription Audit
# ─────────────────────────────────────────────────────────────────────

@app.post(
    "/subscriptions/audit",
    response_model=SubscriptionAuditResponse,
    tags=["Subscriptions"],
    summary="AI-powered scan of the user's financial footprint for active subscriptions",
)
async def subscription_audit() -> SubscriptionAuditResponse:
    """
    **One-Click AI Subscription Audit**

    Simulates parsing the user's bank statements, UPI autopay mandates,
    and SMS transaction alerts to detect active retail subscriptions.

    For each detected subscription, the response includes:
    - Current retail price the user is paying
    - Proposed Subspace group-split price
    - Monthly and percentage savings

    In production this would integrate with Account Aggregator (AA)
    APIs and SMS parsing pipelines.
    """
    now = _now()

    subs_out: list[DetectedSubscription] = []
    total_retail = 0.0
    total_optimized = 0.0

    for sub in _detected_subscriptions:
        savings = round(sub["retail_price"] - sub["subspace_split_price"], 2)
        savings_pct = round((savings / sub["retail_price"]) * 100, 1)

        # If already optimized, the user is paying the split price.
        current_retail = sub["subspace_split_price"] if sub["is_optimized"] else sub["retail_price"]
        total_retail += current_retail
        total_optimized += sub["subspace_split_price"]

        subs_out.append(DetectedSubscription(
            sub_id=sub["sub_id"],
            service_name=sub["service_name"],
            category=sub["category"],
            icon_emoji=sub["icon_emoji"],
            retail_price=sub["retail_price"],
            subspace_split_price=sub["subspace_split_price"],
            monthly_savings=savings,
            savings_pct=savings_pct,
            billing_cycle=sub["billing_cycle"],
            detected_via=sub["detected_via"],
            is_optimized=sub["is_optimized"],
        ))

    total_monthly_savings = round(total_retail - total_optimized, 2)
    total_annual_savings = round(total_monthly_savings * 12, 2)

    optimized_count = sum(1 for s in _detected_subscriptions if s["is_optimized"])
    remaining = len(_detected_subscriptions) - optimized_count

    scan_summary = (
        f"Detected {len(_detected_subscriptions)} active subscriptions. "
        f"{optimized_count} already optimized via Subspace, "
        f"{remaining} can still be optimized to save ₹{total_monthly_savings:,.2f}/month "
        f"(₹{total_annual_savings:,.2f}/year)."
    )

    return SubscriptionAuditResponse(
        user_id=_wallet["user_id"],
        total_retail_spend=round(total_retail, 2),
        total_optimized_spend=round(total_optimized, 2),
        total_monthly_savings=total_monthly_savings,
        total_annual_savings=total_annual_savings,
        subscriptions=subs_out,
        scan_summary=scan_summary,
        scanned_at=now.isoformat(),
    )


# ─────────────────────────────────────────────────────────────────────
# Endpoint 5 — Optimize Subscription (Route to Subspace Pool)
# ─────────────────────────────────────────────────────────────────────

@app.post(
    "/subscriptions/optimize",
    response_model=OptimizeResponse,
    tags=["Subscriptions"],
    summary="Route a detected subscription into a Subspace group-split pool",
)
async def subscription_optimize(payload: OptimizeRequest) -> OptimizeResponse:
    """
    **One-Click Subscription Optimization**

    Takes a detected subscription ID and simulates migrating it into
    a Subspace group-split pool.  The user immediately starts paying
    the lower split price instead of full retail.

    In production this would:
    1. Cancel or modify the user's existing UPI autopay mandate.
    2. Enroll them into a Subspace-managed family/group plan.
    3. Set up a new split-amount autopay for their share.
    """
    # Find the subscription in the mock database.
    target = None
    for sub in _detected_subscriptions:
        if sub["sub_id"] == payload.sub_id:
            target = sub
            break

    if not target:
        raise HTTPException(
            status_code=404,
            detail=f"Subscription {payload.sub_id} not found.",
        )

    if target["is_optimized"]:
        raise HTTPException(
            status_code=409,
            detail=f"{target['service_name']} is already optimized via Subspace.",
        )

    # Mark as optimized.
    target["is_optimized"] = True

    # Generate a pool ID.
    pool_id = f"POOL-{uuid.uuid4().hex[:8].upper()}"

    savings = round(target["retail_price"] - target["subspace_split_price"], 2)

    return OptimizeResponse(
        sub_id=target["sub_id"],
        service_name=target["service_name"],
        previous_price=target["retail_price"],
        new_price=target["subspace_split_price"],
        monthly_savings=savings,
        pool_id=pool_id,
        message=(
            f"Successfully routed {target['service_name']} to Subspace pool "
            f"{pool_id}. You are now saving ₹{savings:,.2f}/month."
        ),
    )


# ─────────────────────────────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health_check():
    """Simple liveness probe."""
    return {
        "status": "ok",
        "service": "subspace-trust-shield",
        "timestamp": _now().isoformat(),
    }
