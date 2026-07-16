# DTB Till Moja — Testing Guide

## Overview

This guide covers how to test the DTB Till Moja integration using:

1. **Sandbox Mock Server** — Simulates the DTB Till Moja API locally
2. **Odoo Test Suite** — 22 automated unit tests
3. **CLI Tests** — Quick end-to-end smoke tests
4. **Manual curl Commands** — Ad-hoc testing of individual flows

---

## 1. Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10+ | For sandbox server |
| Flask | 3.0+ | `pip install flask requests` |
| Odoo | 19.0 | Running with this module installed |
| Odoo DB | postgres | With `mobipine_odoo_dtb_intergration` installed |

### 1.1 Install Sandbox Dependencies

```bash
cd /home/wyckie/Desktop/ODOO/POS/custom_addons/mobipine_odoo_dtb_intergration/sandbox
pip install -r requirements.txt
```

### 1.2 Start Odoo

```bash
cd /home/wyckie/Desktop/ODOO/POS
docker compose up -d

# Install/upgrade the module
docker exec pos_odoo_platform odoo server \
  -d postgres \
  -u mobipine_odoo_dtb_intergration \
  --stop-after-init \
  --http-port=8069
```

---

## 2. Running Odoo Unit Tests

### 2.1 All Tests

```bash
cd /home/wyckie/Desktop/ODOO/POS/custom_addons/mobipine_odoo_dtb_intergration
./run_tests.sh
```

Expected output: **22 tests, 0 failures**

### 2.2 Specific Test Class

```bash
docker exec pos_odoo_platform odoo server \
  -d postgres \
  -u mobipine_odoo_dtb_intergration \
  --test-tags ":TestDtbTillConfig" \
  --stop-after-init \
  --http-port=8069
```

### 2.3 Test Classes Reference

| Test Class | File | Tests | What It Covers |
|---|---|---|---|
| `TestDtbTillConfig` | `test_dtb_till.py` | 2 | Till creation, field values, defaults |
| `TestDtbTransactionLog` | `test_dtb_transaction.py` | 3 | Transaction logging, default state, xref uniqueness |
| `TestDtbReferenceValidation` | `test_dtb_controller.py` | 3 | Invoice reference match, not found, amount mismatch |
| `TestDtbCallbackProcessing` | `test_dtb_controller.py` | 4 | Transaction log, idempotency, invoice reconciliation, mismatch |
| `TestDtbStkConfig` | `test_dtb_stk.py` | 2 | STK fields on till and transaction models |
| `TestDtbStkPush` | `test_dtb_stk.py` | 3 | STK push request, pending transaction, DTB rejection |
| `TestDtbStkCallback` | `test_dtb_stk.py` | 5 | Daraja callback, idempotency, failed payment, unknown ID, flat format |

---

## 3. Starting the Sandbox Server

```bash
# Terminal 1: Start the sandbox
cd /home/wyckie/Desktop/ODOO/POS/custom_addons/mobipine_odoo_dtb_intergration/sandbox

# Set your Odoo URL (default: http://localhost:8569)
export ODOO_BASE_URL=http://localhost:8569
export DTB_API_KEY=sandbox_test_api_key_123

python mock_dtb_server.py
```

Expected output:
```
DTB Till Moja Sandbox running on http://0.0.0.0:5050
Odoo base URL: http://localhost:8069
API Key: sandbox_test_api_key_123

── Till Moja (C2B) Endpoints ──
  All /till-moja/* endpoints for till management
  POST /sandbox/send-payment         — Send C2B callback
  POST /sandbox/trigger-payment-flow — Full C2B flow

── STK Push (B2C) Endpoints ──
  POST /till-moja/stk-push           — Initiate STK Push (called by Odoo)
  POST /sandbox/send-stk-push        — Simulate Odoo→DTB STK + callback to Odoo
  POST /sandbox/simulate-stk-flow    — Full STK flow with auto-callback

── Management ──
  POST /sandbox/reset                — Reset all data
  GET  /sandbox/status               — Server status
```

### 3.1 Sandbox Status Check

```bash
curl http://localhost:5050/sandbox/status
```

Expected:
```json
{
  "status": "running",
  "odo_base_url": "http://localhost:8069",
  "tills_registered": 0,
  "stk_pending": 0,
  "tills": [],
  "stk_checkouts": []
}
```

---

## 4. Setup: Create Test Data in Odoo

Before running any flow tests, create test invoices in Odoo.

### 4.1 Create Test Products (if needed)

```python
# Odoo Python console or a test script
product = self.env['product.product'].create({
    'name': 'Test Consultation',
    'sale_ok': True,
    'lst_price': 1500.0,
})
```

### 4.2 Create Test Invoices

```python
partner = self.env['res.partner'].create({'name': 'Test Patient'})
invoice = self.env['account.move'].create({
    'move_type': 'out_invoice',
    'partner_id': partner.id,
    'payment_reference': 'INV/2026/001',
    'invoice_line_ids': [(0, 0, {
        'product_id': product.id,
        'quantity': 1,
        'price_unit': 1500.0,
    })],
})
invoice.action_post()
```

### 4.3 Create DTB Till Config

Via **Accounting → Configuration → DTB Moja → Till Configuration**:

| Field | Value |
|---|---|
| Name | `Test Till` |
| Company | Your company |
| Till Number | `100004` |
| API User ID | `API_M247` |
| API Password | `qOw1EaF23xvf=` |
| API Key | `sandbox_test_api_key_123` |
| Journal | Create a Bank journal named `DTB Bank` |

> **Important**: The `API Key` in your till config must match the `DTB_API_KEY` used by the sandbox server. The sandbox default is `sandbox_test_api_key_123`.

---

## 5. Till Moja (C2B) Flow Testing

The C2B flow simulates a customer paying manually via M-Pesa Paybill/Till.
DTB receives the payment and sends a callback to Odoo.

### 5.1 Flow A: Reference Validation Only

Tests that DTB can validate an invoice reference before accepting payment.

```bash
# DTB calls Odoo to verify an invoice exists and amount matches
curl -X GET "http://localhost:8069/api/dtb/validate-reference?tillNumber=100004&referenceNumber=INV/2026/001&transactionAmount=1500" \
  -H "Authorization: Bearer sandbox_test_api_key_123"
```

**Expected (invoice found, amount matches):**
```json
{
  "till_number": "100004",
  "reference_id": "INV/2026/001",
  "value_1": "Test Patient",
  "value_2": "INV/2026/001",
  "value_3": "1500.0",
  "value_4": "",
  "value_5": ""
}
```

**Test variations:**

```bash
# Invoice not found
curl "http://localhost:8069/api/dtb/validate-reference?tillNumber=100004&referenceNumber=NONEXISTENT&transactionAmount=100" \
  -H "Authorization: Bearer sandbox_test_api_key_123"
# → 404 {"error": "Reference not found or amount mismatch"}

# Amount mismatch
curl "http://localhost:8069/api/dtb/validate-reference?tillNumber=100004&referenceNumber=INV/2026/001&transactionAmount=500" \
  -H "Authorization: Bearer sandbox_test_api_key_123"
# → 404 {"error": "Reference not found or amount mismatch"}

# No auth header
curl "http://localhost:8069/api/dtb/validate-reference?tillNumber=100004&referenceNumber=INV/2026/001&transactionAmount=1500"
# → 401 {"error": "Unauthorized"}
```

### 5.2 Flow B: C2B Payment Callback (Manual)

Sends a simulated Till Moja callback to Odoo.

```bash
curl -X POST "http://localhost:8569/api/dtb/callback/notification" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sandbox_test_api_key_123" \
  -d '{
    "xref": "EXT-TEST-C2B-001",
    "cbs_reference": "CBS1234567890",
    "cbs_module": "RT",
    "account_number": "0012870005",
    "branch_code": "023",
    "currency": "KES",
    "transaction_time": "20260710 14:30:00",
    "value_date": "20260710",
    "amount": "1500",
    "reversal_indicator": "n",
    "debit_credit_indicator": "C",
    "exchange_rate": "1",
    "financial_year": "FY2026",
    "customer_name": "John Doe",
    "customer_mobile": "254700000000",
    "narration": "INV/2026/001"
  }'
```

**Expected (invoice found):**
```json
{
  "xref": "EXT-TEST-C2B-001",
  "user_reference": "BANK/2026/00001",
  "ack_code": "00",
  "ack_description": "SUCCESS"
}
```

**Verify in Odoo:**
- Check **Accounting → DTB Moja → Transaction Log** for a record with `state=processed`
- Check the invoice `INV/2026/001` should now show as **Paid**

### 5.3 Flow C: C2B Idempotency Test

Send the same callback again — Odoo should return success without duplicating.

```bash
# Re-send the exact same payload from Flow B
curl -X POST "http://localhost:8069/api/dtb/callback/notification" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sandbox_test_api_key_123" \
  -d '{"xref":"EXT-TEST-C2B-001","cbs_reference":"CBS1234567890","amount":"1500","narration":"INV/2026/001"}'
```

**Expected (idempotent):**
```json
{
  "xref": "EXT-TEST-C2B-001",
  "user_reference": "EXT-TEST-C2B-001",
  "ack_code": "00",
  "ack_description": "SUCCESS"
}
```

Verify only **1** transaction log record exists for `EXT-TEST-C2B-001`.

### 5.4 Flow D: C2B Unmatched Reference

When the customer enters a wrong invoice reference, the payment goes to `mismatch`.

```bash
curl -X POST "http://localhost:8069/api/dtb/callback/notification" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sandbox_test_api_key_123" \
  -d '{
    "xref": "EXT-TEST-C2B-MISMATCH",
    "cbs_reference": "CBS9999999999",
    "amount": "5000",
    "narration": "WRONG-REF-NO-INVOICE",
    "customer_name": "Unknown Payer"
  }'
```

**Expected:**
```json
{
  "xref": "EXT-TEST-C2B-MISMATCH",
  "user_reference": "MANUAL_RECONCILIATION_REQUIRED",
  "ack_code": "00",
  "ack_description": "UNMATCHED_REFERENCE"
}
```

**Verify:**
- Transaction log shows `state=mismatch`, `error_reason='Invoice not found'`
- Manager must manually reconcile via the Transaction Log form

### 5.5 Flow E: Full C2B via Sandbox (Automated)

Uses the sandbox to simulate the complete C2B flow end-to-end.

```bash
# 1. Check sandbox is running
curl http://localhost:5050/sandbox/status

# 2. Ensure invoice INV/2026/001 exists in Odoo and is posted

# 3. Trigger full C2B flow via sandbox
curl -X POST http://localhost:5050/sandbox/trigger-payment-flow \
  -H "Content-Type: application/json" \
  -d '{
    "till_number": "100004",
    "amount": "1500",
    "narration": "INV/2026/001",
    "customer_name": "Sandbox Patient",
    "customer_mobile": "254700000000"
  }'
```

**Expected:**
```json
{
  "status": "payment_sent",
  "odoo_response": {
    "ack_code": "00",
    "ack_description": "SUCCESS"
  }
}
```

---

## 6. STK Push (B2C) Flow Testing

The STK Push flow simulates Odoo initiating a payment by sending a push
notification to the customer's phone.

### 6.1 Prerequisites: STK Test Data

Ensure your till config has STK fields filled:
- **STK Push URL**: `http://localhost:5050/till-moja/stk-push`
- **STK Callback URL**: `http://localhost:8069/api/dtb/stk-callback`

### 6.2 Flow A: STK Push Initiation (Via Odoo Method)

You can test the STK push method directly in Odoo's technical console:

```python
till = self.env['dtb.moja.till'].search([('till_number', '=', '100004')], limit=1)
result = self.env['dtb.moja.validation']._stk_push_request(
    till.id,
    amount=1500.0,
    phone_number='254790999957',
    narration='INV/STK/001',
    partner_name='Test Patient',
)
print(result)
# → {'checkout_request_id': 'ws_CO_...', 'xref': 'EXT-...', 'response_code': '000'}
```

**Verify:**
- Transaction log has a new record with `state=pending_stk`
- `payment_method='stk_push'`
- `checkout_request_id` is populated

### 6.3 Flow B: STK Callback Success (Daraja Format)

Send a simulated Daraja-style STK callback to Odoo.

First create a pending STK transaction with a known `checkout_request_id`:

```bash
# Create the pending transaction via Odoo API (or do it manually in Odoo)
# Then send the Daraja callback:
curl -X POST "http://localhost:8069/api/dtb/stk-callback" \
  -H "Content-Type: application/json" \
  -d '{
    "Body": {
      "stkCallback": {
        "MerchantRequestID": "29115-34620561-1",
        "CheckoutRequestID": "ws_CO_DMZ_STK_TEST_001",
        "ResultCode": 0,
        "ResultDesc": "The service request is processed successfully.",
        "CallbackMetadata": {
          "Item": [
            {"Name": "Amount", "Value": 1500.0},
            {"Name": "MpesaReceiptNumber", "Value": "RGH9876543"},
            {"Name": "PhoneNumber", "Value": 254790999957}
          ]
        }
      }
    }
  }'
```

> **Note**: The `CheckoutRequestID` must match a transaction with `state=pending_stk` in Odoo.

**Expected (success):**
```json
{
  "ack_code": "00",
  "ack_description": "SUCCESS"
}
```

**Verify:**
- Transaction `state` changed from `pending_stk` to `processed`
- `mpesa_receipt` populated with `RGH9876543`
- Invoice reconciled

### 6.4 Flow C: STK Callback Failed Payment

Simulate the customer cancelling the STK prompt.

```bash
curl -X POST "http://localhost:8069/api/dtb/stk-callback" \
  -H "Content-Type: application/json" \
  -d '{
    "Body": {
      "stkCallback": {
        "CheckoutRequestID": "ws_CO_DMZ_STK_FAIL_001",
        "ResultCode": 1032,
        "ResultDesc": "Request cancelled by user",
        "CallbackMetadata": {"Item": []}
      }
    }
  }'
```

**Expected:**
```json
{
  "ack_code": "00",
  "ack_description": "FAILED"
}
```

**Verify:**
- Transaction `state` = `failed`
- `stk_result_code` = `1032`
- No payment created, invoice unchanged

### 6.5 Flow D: STK Callback Unknown Checkout ID

Simulate DTB sending a callback for a transaction Odoo doesn't know about.

```bash
curl -X POST "http://localhost:8069/api/dtb/stk-callback" \
  -H "Content-Type: application/json" \
  -d '{
    "Body": {
      "stkCallback": {
        "CheckoutRequestID": "ws_CO_NEVER_EXISTED",
        "ResultCode": 0,
        "ResultDesc": "SUCCESS",
        "CallbackMetadata": {"Item": []}
      }
    }
  }'
```

**Expected:**
```json
{
  "ack_code": "99",
  "ack_description": "TRANSACTION_NOT_FOUND"
}
```

### 6.6 Flow E: Full STK via Sandbox (Automated)

Uses the sandbox to simulate a complete STK flow.

```bash
curl -X POST http://localhost:5050/sandbox/simulate-stk-flow \
  -H "Content-Type: application/json" \
  -d '{
    "till_number": "100004",
    "amount": "1500",
    "phone_number": "254790999957",
    "narration": "INV/STK/002",
    "callback_url": "http://localhost:8069/api/dtb/stk-callback"
  }'
```

**Expected:**
```json
{
  "status": "stk_flow_started",
  "checkout_request_id": "ws_CO_FLOW_...",
  "note": "Daraja-style callback will be sent to Odoo in ~1 second"
}
```

After 1 second, the sandbox automatically sends a Daraja callback to Odoo.
Check the transaction log for a record that transitions from `pending_stk` to `processed`.

### 6.7 Flow F: STK via Sandbox with Auto-Callback

Simulates Odoo sending an STK push to DTB, then automatically sends the
Daraja callback back to Odoo.

```bash
curl -X POST http://localhost:5050/sandbox/send-stk-push \
  -H "Content-Type: application/json" \
  -d '{
    "till": {
      "till_number": "100004",
      "user_id": "API_M247",
      "password": "qOw1EaF23xvf="
    },
    "amount": "1500",
    "phone_number": "254790999957",
    "narration": "INV/STK/003",
    "callback_url": "http://localhost:8069/api/dtb/stk-callback",
    "auto_callback": true
  }'
```

> **Note**: This endpoint simulates the full Odoo→DTB→Safaricom→Phone→Callback flow.
> Set `auto_callback: true` to have the sandbox send the Daraja callback automatically.

---

## 7. Sandbox CLI Test (Quick Smoke Test)

Run the full CLI test to validate both C2B and STK flows:

```bash
cd /home/wyckie/Desktop/ODOO/POS/custom_addons/mobipine_odoo_dtb_intergration/sandbox
export ODOO_BASE_URL=http://localhost:8069
export DTB_API_KEY=sandbox_test_api_key_123

python mock_dtb_server.py --cli-test
```

The CLI test runs these steps:

| Step | Flow | Action |
|---|---|---|
| 1 | Setup | Creates a till |
| 2 | C2B | Validates reference via Odoo |
| 3 | C2B | Sends payment callback to Odoo |
| 4 | C2B | Tests idempotency (resends same xref) |
| 5 | STK | Simulates STK push + sends Daraja callback |
| 6 | Summary | Prints sandbox status |

---

## 8. Edge Cases & Error Scenarios

### 8.1 Duplicate xref (C2B)

```bash
# Send same xref twice
curl -X POST "http://localhost:8069/api/dtb/callback/notification" \
  -H "Content-Type: application/json" \
  -d '{"xref":"EXT-DEDUP-TEST","amount":"100","narration":"TEST"}'
# → state=draft (first time)

curl -X POST "http://localhost:8069/api/dtb/callback/notification" \
  -H "Content-Type: application/json" \
  -d '{"xref":"EXT-DEDUP-TEST","amount":"100","narration":"TEST"}'
# → ack=00, only 1 record created
```

### 8.2 Duplicate checkout_request_id (STK)

Odoo's `_process_stk_callback` checks `tx.state in ('processed',)` and returns
success without re-processing.

### 8.3 Missing API Key

```bash
curl "http://localhost:8069/api/dtb/validate-reference?tillNumber=100004&referenceNumber=INV/2026/001&transactionAmount=1500"
# → 401 {"error": "Unauthorized"}
```

### 8.4 Invalid Amount

```bash
curl -X POST "http://localhost:8069/api/dtb/callback/notification" \
  -H "Content-Type: application/json" \
  -d '{"xref":"EXT-BAD-AMOUNT","amount":"-100","narration":"INV/2026/001"}'
# → Transaction created (amount can be negative for reversals)
# → State depends on whether invoice match succeeds
```

### 8.5 Malformed JSON

```bash
curl -X POST "http://localhost:8069/api/dtb/callback/notification" \
  -H "Content-Type: application/json" \
  -d 'not json at all'
# → Odoo returns 400 Bad Request
```

### 8.6 Sandbox Reset

```bash
# Reset all sandbox data between test runs
curl -X POST http://localhost:5050/sandbox/reset
```

---

## 9. Test Matrix

| # | Scenario | Flow | How to Test | Expected Result |
|---|---|---|---|---|
| 1 | Till config created | Setup | Odoo UI or API | Fields saved, defaults applied |
| 2 | Validate invoice match | C2B | `GET /api/dtb/validate-reference` | 200 with invoice values |
| 3 | Validate invoice not found | C2B | Same endpoint, bad ref | 404 None |
| 4 | Validate amount mismatch | C2B | Same endpoint, wrong amount | 404 None |
| 5 | Validate unauthorized | C2B | No auth header | 401 |
| 6 | C2B payment callback | C2B | `POST /api/dtb/callback/notification` | 200, tx created, invoice paid |
| 7 | C2B idempotency | C2B | Resend same xref | 200, no duplicate |
| 8 | C2B unmatched reference | C2B | Unknown narration | tx state=mismatch |
| 9 | STK Push initiation | STK | Call `_stk_push_request()` | tx state=pending_stk |
| 10 | STK callback success | STK | Daraja format `POST /api/dtb/stk-callback` | tx state=processed, invoice paid |
| 11 | STK callback failed | STK | Daraja ResultCode=1032 | tx state=failed |
| 12 | STK callback unknown ID | STK | Unknown CheckoutRequestID | ack=TRANSACTION_NOT_FOUND |
| 13 | STK idempotency | STK | Resend same callback | 200, no duplicate |
| 14 | Sandbox full C2B flow | C2B | `POST /sandbox/trigger-payment-flow` | Odoo receives callback |
| 15 | Sandbox full STK flow | STK | `POST /sandbox/simulate-stk-flow` | Odoo receives Daraja callback |
| 16 | Sandbox CLI test | Both | `python mock_dtb_server.py --cli-test` | All 6 steps pass |

---

## 10. Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| Sandbox returns "Odoo unreachable" | Odoo not running | `docker compose up -d`, check `ODOO_BASE_URL` |
| 401 on validate-reference | API Key mismatch | Ensure till `api_key` = `DTB_API_KEY` env var |
| C2B callback returns `UNMATCHED_REFERENCE` | Invoice not found/not posted | Create invoice with `payment_reference` matching `narration` |
| STK callback returns `TRANSACTION_NOT_FOUND` | No pending transaction with that checkout_request_id | Create pending_stk transaction first |
| No `dtb.moja.transaction` records visible | No access rights | Assign `Accountant` or `Invoicing` role to user |
| Odoo tests fail | Module not installed | Run `-u mobipine_odoo_dtb_intergration` first |
| `_stk_push_request` times out | Sandbox not running | Start sandbox on port 5050 |
| Unique constraint error on xref | Duplicate xref in test | Use unique xrefs per test run |
