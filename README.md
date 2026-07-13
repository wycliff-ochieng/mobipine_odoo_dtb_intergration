# DTB Till Moja Integration

[![Odoo](https://img.shields.io/badge/Odoo-19.0-714b67?logo=odoo)](https://www.odoo.com)
[![License](https://img.shields.io/badge/license-LGPL--3-blue)](LICENSE)
[![Version](https://img.shields.io/badge/version-19.0.1.0.0-green)](__manifest__.py)

Accept M-Pesa payments through DTB Till Moja — validate invoice references in real time, reconcile payments automatically, and initiate STK Push requests directly from the invoice form.

---

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Architecture & Design Decisions](#architecture--design-decisions)
  - [Why Three Separate Endpoints](#why-three-separate-endpoints)
  - [Sudo-Only Webhook Processing](#sudo-only-webhook-processing)
  - [Idempotency by Design](#idempotency-by-design)
  - [Two Payload Formats for STK](#two-payload-formats-for-stk)
- [Complete Processing Flow](#complete-processing-flow)
  - [Flow 1: Till Moja (C2B) — Customer Pays via M-Pesa Paybill](#flow-1-till-moja-c2b--customer-pays-via-m-pesa-paybill)
  - [Flow 2: STK Push (B2C) — Staff Initiates Payment Request](#flow-2-stk-push-b2c--staff-initiates-payment-request)
  - [Flow 3: Webhook → Payment → Reconciliation](#flow-3-webhook--payment--reconciliation)
- [API Reference](#api-reference)
  - [GET /api/dtb/validate-reference](#get-apidtbvalidate-reference)
  - [POST /api/dtb/callback/notification](#post-apidtbcallbacknotification)
  - [POST /api/dtb/stk-callback](#post-apidtbvalidatereference)
- [STK Push Wizard](#stk-push-wizard)
- [Audit Log & Models](#audit-log--models)
- [Error Scenarios & Recovery](#error-scenarios--recovery)
- [Configuration](#configuration)
  - [Till Setup](#till-setup)
  - [System Parameters](#system-parameters)
- [Sandbox Testing](#sandbox-testing)
- [Security](#security)
- [Dependencies](#dependencies)
- [Installation](#installation)
- [Performance Characteristics](#performance-characteristics)
- [Development & Testing](#development--testing)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Overview

This module connects Odoo to the Diamond Trust Bank (Kenya) Till Moja payment platform, enabling automated M-Pesa payment processing for invoices.

**What it does at a glance:**

| Capability | How it works |
|---|---|
| **Reference validation** | DTB queries Odoo before accepting a payment to verify the invoice exists and the amount matches |
| **C2B (Till Moja)** | DTB sends a callback when a customer pays via M-Pesa Paybill; Odoo matches and reconciles automatically |
| **STK Push (B2C)** | Staff clicks "Send STK Push" from the invoice form; customer receives M-Pesa prompt on their phone |
| **Auto-reconciliation** | Incoming payments are matched to invoices, an `account.payment` is created, posted, and reconciled — all in one atomic flow |
| **Manual reconciliation queue** | Payments with no matching invoice are recorded and flagged for manual review |
| **Sandbox simulator** | Flask mock server for end-to-end testing without a live DTB account |

---

## Quick Start

1. **Configure a Till** — *DTB Moja → Till Configuration → New* with your DTB credentials, till number, and payment journal
2. **Post an Invoice** — *Invoicing → Customers → Invoices* — ensure `payment_reference` is set
3. **Test C2B flow** — use the sandbox to simulate a payment callback:
   ```bash
   curl -X POST http://localhost:5050/sandbox/trigger-payment-flow \
     -H "Content-Type: application/json" \
     -d '{"till_number":"100004","amount":"20","narration":"INV/2026/00013"}'
   ```
4. **Test STK flow** — open a posted invoice, click **Send STK Push**, enter the phone number
5. **Verify** — the invoice's payment state transitions to `paid` or `in_payment` with a reconciled `account.payment`

---

## Architecture & Design Decisions

### Why Three Separate Endpoints

The DTB platform uses a two-phase payment model (validate → settle). Rather than cramming everything into one route, the module mirrors DTB's own separation:

| Endpoint | Phase | Called by | Purpose |
|---|---|---|---|
| `GET /api/dtb/validate-reference` | Pre-payment | DTB Gateway | Verify invoice exists and amount matches before accepting payment |
| `POST /api/dtb/callback/notification` | Settlement | DTB Gateway | Receive confirmed payment and reconcile |
| `POST /api/dtb/stk-callback` | STK Result | DTB/Safaricom | Receive STK push outcome (success/failure) |

This separation keeps each endpoint focused, idempotent, and independently testable. The `validate-reference` endpoint uses Bearer token auth; the two callback endpoints use `auth='none'` since they are invoked by DTB's servers, not a browser session.

### Sudo-Only Webhook Processing

Both callback endpoints use `auth='none'` — there is no authenticated Odoo user. All database operations inside the callback handlers run via `.sudo()`. This means:

- No session, no user — `request.env.user` is an empty recordset
- Any code path that calls `self.env.user.has_group()` (e.g., `pos_sale`'s `reflect_cancelled_sol`) will crash

The module overrides `_post_process()` on `payment.transaction` to detect this condition and rebind to `SUPERUSER_ID` before chaining to the standard Odoo payment finalization chain:

```python
def _post_process(self):
    if not self.env.user:
        self = self.with_user(SUPERUSER_ID)
    return super()._post_process()
```

### Idempotency by Design

Both callback endpoints check for existing transactions before creating new ones:

- **C2B callback:** Duplicate `xref` → return `SUCCESS` with no side effects
- **STK callback:** Transaction already `done` → return `SUCCESS`

This means DTB can safely retry callbacks (up to 5 times is common in production) without creating duplicate payments or reconciliations.

### Two Payload Formats for STK

The STK callback parser accepts both the native Safaricom Daraja format (`Body.stkCallback`) and a flat key-value format. The parser tries Daraja first, then falls back:

```python
daraja = payload.get('Body', {}).get('stkCallback', {})
if daraja:
    # Parse Daraja nested format
    ...
else:
    # Parse flat format
    checkout_id = payload.get('checkout_request_id') or payload.get('CheckoutRequestID')
```

This makes the module compatible with both DTB's relayed callbacks (which may transform the payload) and direct Safaricom callbacks.

---

## Complete Processing Flow

### Flow 1: Till Moja (C2B) — Customer Pays via M-Pesa Paybill

```
Customer pays via M-Pesa
        │
        ▼
DTB Gateway receives payment
        │
        ├── (optional) GET /api/dtb/validate-reference
        │       │
        │       ├── Invoice found + amount matches  → 200 (patient/invoice info)
        │       └── Not found or mismatch           → 404 (reject payment)
        │
        ▼
DTB sends POST /api/dtb/callback/notification
        │
        ├── xref already processed? → Return SUCCESS (idempotent)
        │
        └── New callback
                │
                ├── Invoice matched by narration?
                │   ├── Yes → Create payment.transaction
                │   │         → tx._set_done()
                │   │         → tx._post_process()
                │   │             → Create account.payment (inbound, posted)
                │   │             → Reconcile with invoice
                │   │             → Return SUCCESS
                │   │
                │   └── No  → Create payment.transaction (unlinked)
                │             → tx._set_done()
                │             → Return UNMATCHED_REFERENCE
                │               (manual reconciliation required)
                │
                └── Return 200 (DTB expects 200 even on errors)
```

### Flow 2: STK Push (B2C) — Staff Initiates Payment Request

```
Staff opens posted invoice
        │
        ▼
Clicks "Send STK Push"
        │
        ├── Invoice already paid? → UserError blocked
        ├── No active till with STK URL? → UserError blocked
        │
        └── Wizard opens
                │
                ├── Staff enters phone number
                │
                ▼
        Odoo sends POST {stk_push_url}
                │
                ├── Connection error → UserError
                ├── DTB rejects → UserError
                │
                └── Success
                        │
                        ▼
                DTB sends STK push to customer phone
                        │
                        ├── Customer pays
                        │   └── DTB calls POST /api/dtb/stk-callback
                        │       → Match by checkout_request_id
                        │       → Create payment, reconcile
                        │
                        └── Customer fails/cancels
                            └── DTB calls POST /api/dtb/stk-callback
                                → Match by checkout_request_id
                                → Set transaction to error state
```

### Flow 3: Webhook → Payment → Reconciliation

When `_post_process()` runs (called from either callback), the payment creation and reconciliation chain executes:

```
tx._post_process()
  │
  ├── tx._create_payment()
  │     │
  │     ├── Find till → fallback: active till with journal
  │     ├── Find journal → fallback: any bank journal
  │     ├── Find partner → fallback: "Unreconciled DTB Customer" (auto-created)
  │     ├── Create account.payment (inbound, posted)
  │     └── Reconcile: match payment line with invoice line
  │           on the receivable account
  │
  └── Invoice payment_state updates to 'paid' or 'in_payment'
```

---

## API Reference

### `GET /api/dtb/validate-reference`

Pre-payment invoice validation. Called by DTB to check the reference before accepting a payment.

**Auth:** Bearer token (`Authorization: Bearer {api_key}` matched against `dtb.moja.till.api_key`)

| Parameter | Type | Required | Description |
|---|---|---|---|
| `tillNumber` | string | Yes | DTB till number |
| `referenceNumber` | string | Yes | Invoice `payment_reference` |
| `transactionAmount` | string | No | Amount being paid (default `"0"`) |

**Success `200`:**

```json
{
  "till_number": "100004",
  "reference_id": "INV/2026/00013",
  "value_1": "Abdiladif Ibrahim",
  "value_2": "INV/2026/00013",
  "value_3": "20.0",
  "value_4": "",
  "value_5": ""
}
```

| Error | Status | Body |
|---|---|---|
| No/invalid API key | 401 | `{"error": "Unauthorized"}` |
| Missing params | 400 | `{"error": "Missing required parameters"}` |
| Invoice not found or amount mismatch | 404 | `{"error": "Reference not found or amount mismatch"}` |
| Unhandled exception | 500 | `{"error": "Internal server error"}` |

**Amount matching:** Uses Python's `math.isclose(amt, residual, rel_tol=1e-9)` — floating-point safe comparison.

**Invoice search domain:**
```
payment_reference = referenceNumber
state = 'posted'
payment_state NOT IN ('paid', 'in_payment')
```

---

### `POST /api/dtb/callback/notification`

C2B payment settlement callback. Receives confirmed payments from DTB.

**Auth:** `auth='none'` (no authentication — DTB server-to-server)

**Request body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `xref` | string | **Yes** | DTB unique trace reference (idempotency key) |
| `amount` | string/number | **Yes** | Payment amount |
| `narration` | string | **Yes** | Invoice reference the customer entered during payment |
| `cbs_reference` | string | No | DTB core banking reference |
| `customer_name` | string | No | Payer name |
| `customer_mobile` | string | No | Payer phone |
| `account_number` | string | No | Till number (used for matching on mismatch) |
| `currency` | string | No | `"KES"` |
| `cbs_module` | string | No | Core banking module |
| `branch_code` | string | No | Branch |
| `transaction_time` | string | No | `YYYYMMDD HH:mm:ss` |
| `value_date` | string | No | `YYYYMMDD` |
| `reversal_indicator` | string | No | `"y"`/`"n"` |
| `debit_credit_indicator` | string | No | `"C"` (credit) |
| `exchange_rate` | string | No | `"1"` |
| `financial_year` | string | No | `"FY2026"` |

**Response (`ack_code`):**

| `ack_code` | `ack_description` | Meaning |
|---|---|---|
| `00` | `SUCCESS` | Payment matched to invoice and reconciled |
| `00` | `UNMATCHED_REFERENCE` | No invoice found — manual reconciliation needed |
| `99` | `INTERNAL_ERROR` | Server error — check logs |

All responses return HTTP 200 (DTB expects 200 to acknowledge receipt).

---

### `POST /api/dtb/stk-callback`

STK Push result callback. Receives the outcome of an M-Pesa STK Push.

**Auth:** `auth='none'`

**Request body — Daraja format (native Safaricom):**

```json
{
  "Body": {
    "stkCallback": {
      "CheckoutRequestID": "ws_CO_DMZ_1234567890",
      "ResultCode": 0,
      "ResultDesc": "The service request is processed successfully.",
      "CallbackMetadata": {
        "Item": [
          {"Name": "Amount", "Value": 1500.0},
          {"Name": "MpesaReceiptNumber", "Value": "RGH1A2B3C4"},
          {"Name": "PhoneNumber", "Value": 254790999957}
        ]
      }
    }
  }
}
```

**Request body — Flat format:**

```json
{
  "checkout_request_id": "ws_CO_DMZ_1234567890",
  "result_code": "0",
  "mpesa_receipt": "RGH1A2B3C4",
  "phone_number": "254790999957"
}
```

**Response (`ack_code`):**

| `ack_code` | `ack_description` | Meaning |
|---|---|---|
| `00` | `SUCCESS` | Payment successful, invoice reconciled (if matched) |
| `00` | `FAILED` | STK push failed (result code ≠ 0) |
| `99` | `MISSING_CHECKOUT_ID` | Payload unparseable |
| `99` | `TRANSACTION_NOT_FOUND` | No pending transaction matches this checkout ID |
| `99` | `INTERNAL_ERROR` | Server error |

**Result codes treated as success:** `0`, `'0'`, `'00'`, `'000'`.  
**Notable failure code:** `1032` = customer cancelled.

---

## STK Push Wizard

A modal transient model (`dtb.stk.payment.wizard`) accessible from any posted invoice via the **Send STK Push** button.

**Button visibility:**

```
move_type IN ('out_invoice', 'out_refund')
AND state == 'posted'
AND payment_state NOT IN ('paid', 'in_payment')
```

**Wizard fields:**

| Field | Type | Readonly | Source |
|---|---|---|---|
| `invoice_id` | Many2one(`account.move`) | Hidden | Auto-set from context |
| `amount` | Monetary | Yes | From invoice |
| `currency_id` | Many2one(`res.currency`) | Hidden | Related to invoice |
| `phone_number` | Char | No | User input (254 format) |

**Pre-flight checks before sending STK Push:**
1. Invoice not already paid
2. An active till with a configured `stk_push_url` exists

**Narration sent to DTB:** `invoice.payment_reference` or `invoice.name` (fallback).

---

## Audit Log & Models

### `dtb.moja.till` — Till Configuration

| Field | Type | Purpose |
|---|---|---|
| `name` | Char | Display name |
| `company_id` | Many2one | Multi-company isolation |
| `till_number` | Char | DTB till number |
| `user_id` / `password` | Char | DTB API credentials |
| `api_key` | Char | Bearer token for inbound auth |
| `channel` | Char | API channel (default `MBS`) |
| `journal_id` | Many2one | Payment journal for auto-created payments |
| `is_active` | Boolean | Enable/disable |
| `stk_push_url` / `stk_push_callback_url` | Char | STK Push endpoint and callback URL |

### `payment.transaction` — Extended Fields

All DTB-specific fields (`dtb_xref`, `dtb_checkout_request_id`, `dtb_till_id`, `dtb_phone_number`, `dtb_stk_response_code`, `dtb_stk_result_code`, `dtb_stk_result_desc`, `dtb_payment_method`, `dtb_customer_name`) are visible in the **DTB Details** notebook page on the transaction form.

### `account.payment` — Extended Fields

Copies of `dtb_xref`, `dtb_phone_number`, `dtb_customer_name`, and `dtb_till_id` for audit trail.

### `dtb.moja.transaction` — Legacy Audit Log

Defined but not actively written to by the current callback processing code. All transactions are recorded as `payment.transaction` records. The audit log model is reserved for future reconciliation and reporting features.

---

## Error Scenarios & Recovery

| Scenario | What happens | Recovery |
|---|---|---|
| **DTB sends duplicate callback** | Idempotency check catches the duplicate `xref` — returns `SUCCESS` with no side effects | Nothing — already processed. |
| **No invoice matches the narration** | Transaction is created in `done` state but with no invoice linked. Returns `UNMATCHED_REFERENCE`. | Find the transaction in *DTB Moja → Transaction Log*, manually link it to the correct invoice, create and reconcile a payment. |
| **Amount mismatch on validate** | DTB gets `404` and can reject the payment at the till | The customer must pay the correct amount. |
| **Server crash during `_post_process`** | Payment transaction is created but the `account.payment` and reconciliation may not complete | Check *DTB Moja → Transaction Log* for transactions in unexpected state. Manually create payment or re-process. |
| **STK push network timeout** | `UserError` raised — wizard closes with error message | Check till STK URL and network connectivity; retry. |
| **STK callback with unknown checkout ID** | Returns `TRANSACTION_NOT_FOUND` | The transaction may have been deleted or the checkout ID mangled. Check Odoo and DTB logs. |
| **No payment journal configured** | `UserError` during `_create_payment`: `No journal found for payment` | Configure a bank journal on the till record or create a bank journal in Accounting. |
| **No active till for STK Push** | `UserError`: `No active till with STK Push configured` | Create or activate a till with a valid `stk_push_url`. |

---

## Configuration

### Till Setup

Navigate to *DTB Moja → Till Configuration* and create a new till:

| Field | Value | Notes |
|---|---|---|
| Name | Clinic Main Till | Your internal label |
| Company | Your Company | Multi-company |
| Till Number | 100004 | Provided by DTB |
| Active | Yes | |
| Channel | MBS | As provided by DTB |
| Payment Journal | Bank | Journal for auto-created payments |
| API User ID | API_M247 | DTB credential |
| API Password | ******** | DTB credential |
| API Key | sandbox_test... | Bearer token for `validate-reference` (optional) |
| STK Push URL | `https://api.dtbafrica.com/till-moja/stk-push` | For STK Push functionality |
| STK Callback URL | `https://your-odoo.com/api/dtb/stk-callback` | Public URL for STK results |

### System Parameters

| Key | Default | Description |
|---|---|---|
| `mobipine_odoo_dtb_intergration.dtb_base_url` | `https://api.dtbafrica.com` | DTB API base (change for sandbox) |
| `web.base.url` | `http://localhost:8069` | Used to construct STK callback URLs sent to DTB |

---

## Sandbox Testing

The module includes a Flask mock server that simulates the DTB Till Moja API.

```bash
# Start the sandbox
python custom_addons/mobipine_odoo_dtb_intergration/sandbox/mock_dtb_server.py

# Environment variables (optional)
export ODOO_BASE_URL=http://localhost:8569
export DTB_API_KEY=sandbox_test_api_key_123
export DTB_SANDBOX_PORT=5050
```

**Sandbox endpoints:**

| Endpoint | Purpose |
|---|---|
| `POST /sandbox/trigger-payment-flow` | Simulate full C2B flow — creates till + sends callback to Odoo |
| `POST /sandbox/simulate-stk-flow` | Simulate full STK flow — sends Daraja-style callback after 1s |
| `POST /sandbox/send-payment` | Simulate C2B payment callback only |
| `POST /sandbox/send-stk-push` | Simulate STK push with optional auto-callback |
| `GET /sandbox/status` | Sandbox server status |
| `POST /sandbox/reset` | Clear all in-memory data |
| All `/till-moja/*` | Mock DTB till management API |

**Example — full C2B test:**
```bash
curl -X POST http://localhost:5050/sandbox/trigger-payment-flow \
  -H "Content-Type: application/json" \
  -d '{
    "till_number": "100004",
    "amount": "20",
    "narration": "INV/2026/00013",
    "customer_name": "Abdiladif Ibrahim",
    "customer_mobile": "254700000000"
  }'
```

**Example — full STK test:**
```bash
curl -X POST http://localhost:5050/sandbox/simulate-stk-flow \
  -H "Content-Type: application/json" \
  -d '{
    "till_number": "100004",
    "amount": "1500",
    "phone_number": "254790999957",
    "narration": "INV/STK/001",
    "callback_url": "http://localhost:8569/api/dtb/stk-callback"
  }'
```

---

## Security

| Layer | Mechanism |
|---|---|
| **Reference validation** | Bearer token from `dtb.moja.till.api_key` (matched via `search`, not hardcoded) |
| **Webhook endpoints** | `auth='none'` — relies on DTB network security (IP allowlisting, TLS) |
| **Database operations** | All callback processing runs via `.sudo()` — bypasses access rights (necessary since no user session exists) |
| **Credentials** | API passwords stored in plaintext with `password="True"` widget masking |
| **Access control** | Access rights managed through `account.group_account_user` (read on tills and transactions) and `account.group_account_manager` (full CRUD) |

**⚠️ Production consideration:** The callback endpoints (`/api/dtb/callback/notification` and `/api/dtb/stk-callback`) have no built-in authentication. In production, secure them via network-level controls (reverse proxy IP filtering, TLS client certificates) or by adding DTB IP range validation.

---

## Dependencies

| Module | Purpose |
|---|---|
| `base` | Odoo core |
| `account` | Invoice, payment, and reconciliation models |
| `payment` | `payment.transaction`, `payment.provider`, and `payment.method` framework |

---

## Installation

1. Place the `mobipine_odoo_dtb_intergration` directory in your Odoo addons path:
   ```bash
   /mnt/custom-addons/
   └── mobipine_odoo_dtb_intergration/
       ├── __manifest__.py
       ├── models/
       ├── controllers/
       ├── views/
       ├── wizard/
       ├── data/
       ├── security/
       └── sandbox/
   ```
2. Update the apps list (*Apps → Update Apps List*)
3. Search for "DTB Till Moja Integration" and click **Install**
4. Go to *DTB Moja → Till Configuration* and set up your first till

To update after changes:
```bash
odoo -d <database> -u mobipine_odoo_dtb_intergration
```

---

## Performance Characteristics

| Metric | Typical Value |
|---|---|
| Callback processing time | < 500ms per callback (C2B or STK) |
| Payment creation + reconciliation | ~100–300ms per transaction |
| Idempotency check | ~10–20ms (indexed search on `dtb_xref`) |
| Reference validation | ~30–50ms (indexed search on `payment_reference`) |
| STK Push outgoing request | Depends on DTB network latency (typically 500ms–2s) |
| No background threads | All processing is synchronous within the request |

**Bottlenecks:**
- `_post_process()` chains through `pos_online_payment` → `sale` → `account_payment` — each layer adds overhead
- Payment reconciliation involves accounting moves and can slow under high concurrency
- STK Push requests are network-bound (HTTP call to DTB with 15s timeout)

---

## Development & Testing

The module includes unit tests covering the core processing paths:

```bash
# Run all tests
odoo -d <database> --test-tags post_install -u mobipine_odoo_dtb_intergration

# Run specific test file
odoo -d <database> --test-tags mobipine_odoo_dtb_intergration -u mobipine_odoo_dtb_intergration
```

**Test files:**

| File | Coverage |
|---|---|
| `tests/test_dtb_stk.py` | STK Push wizard logic |
| `tests/test_dtb_controller.py` | Controller endpoint handling |
| `tests/test_dtb_transaction.py` | Transaction creation and state transitions |
| `tests/test_dtb_till.py` | Till configuration logic |

**Testing with the sandbox:**

For manual testing, use the Flask mock server as described in the [Sandbox Testing](#sandbox-testing) section. The sandbox can simulate both C2B and STK flows and send callbacks to Odoo.

**Known limitations:**
- The `dtb.moja.transaction` audit log model is defined but not actively written to by the current callback flow
- No background processing — all webhook processing is synchronous (adequate for typical callback volumes)
- No retry queue for failed callbacks (relies on DTB's retry mechanism)

---

## Troubleshooting

| Symptom | Likely Cause | Solution |
|---|---|---|
| `Expected singleton: res.users()` | `_post_process()` called from `auth='none'` context without user rebind | Update to the latest version (includes `_post_process()` override) |
| `Invalid field 'ref' in 'account.payment'` | Using `ref` instead of `payment_reference` field name | Update to the latest version (uses `payment_reference`) |
| Callback returns `INTERNAL_ERROR` | Unhandled exception | Check Odoo server logs for traceback; check the bug log in this repo |
| `No journal found for payment` | Till has no `journal_id` and no bank journal exists | Create a bank journal or assign one to the till |
| `DTB payment provider not found` | Data files not loaded | Upgrade the module (`-u mobipine_odoo_dtb_intergration`) |
| Callback returns `UNMATCHED_REFERENCE` | No invoice matches the narration | Check the invoice's `payment_reference` field; reconcile manually |
| STK Push wizard won't open | Invoice is already paid or not posted | Check invoice `state` and `payment_state` |
| `No active till with STK Push configured` | No till with `is_active=True` and `stk_push_url` set | Configure a till with STK Push URL and mark it active |
| Sandbox returns `Odoo unreachable` | `ODOO_BASE_URL` doesn't match your Odoo instance | Set the correct ODOO_BASE_URL environment variable |
| Payment created but not reconciled | `account.payment` created but reconciliation failed | Check payment and invoice for matching receivable accounts; reconcile manually |

---

## License

This module is licensed under the **LGPL-3**. See the [LICENSE](LICENSE) file for details.
