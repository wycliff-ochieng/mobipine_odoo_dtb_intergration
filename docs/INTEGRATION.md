# DTB Till Moja + M-Pesa Paybill → Odoo Integration

## Architecture Overview

```
                     ┌──────────────────────────────────────────────────────────┐
                     │                    Customer                             │
                     │              (M-Pesa Smartphone)                        │
                     └────────────────────────┬─────────────────────────────────┘
                                              │
                                              │  1. Opens M-Pesa
                                              │     Enters Paybill/Till number
                                              │     Enters Amount
                                              │     Enters Invoice Ref (narration)
                                              ▼
                     ┌──────────────────────────────────────────────────────────┐
                     │              Safaricom M-Pesa (Daraja)                  │
                     │                                                         │
                     │  - Validates customer PIN                               │
                     │  - Deducts from customer M-Pesa wallet                  │
                     │  - Sends payment to DTB Till Moja                       │
                     └────────────────────────┬─────────────────────────────────┘
                                              │
                                              │  2. Payment received
                                              │     DTB validates via Odoo
                                              │     (if validation_url configured)
                                              ▼
                     ┌──────────────────────────────────────────────────────────┐
                     │           DTB TILL MOJA PLATFORM                        │
                     │                                                         │
                     │  - Receives payment from M-Pesa                         │
                     │  - Optionally validates reference w/ Odoo               │
                     │  - Credits merchant till account                        │
                     │  - Sends callback to Odoo                               │
                     └────────────────────────┬─────────────────────────────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────────┐
                    │                         │                             │
                    │  3a. GET               │  3b. POST                   │
                    │  /validate-reference   │  /callback/notification     │
                    │  (pre-payment check)   │  (post-payment)             │
                    ▼                         ▼                             │
         ┌──────────────────────┐  ┌──────────────────────────────────┐     │
         │   ODOO ERP           │  │   ODOO ERP                      │     │
         │                      │  │                                  │     │
         │  Validates:          │  │  1. Create dtb.moja.transaction  │     │
         │  • Invoice reference │  │  2. Match invoice by narration   │     │
         │  • Amount match      │  │  3. Register account.payment     │     │
         │  • Invoice is posted │  │  4. Reconcile with invoice       │     │
         │                      │  │  5. Mark invoice as PAID         │     │
         └──────────────────────┘  └──────────────────────────────────┘     │
                                                                              │
                                                                              ▼
                                                    ┌──────────────────────────┐
                                                    │   dtb.moja.transaction   │
                                                    │                          │
                                                    │  state = 'processed'     │
                                                    │  ✓ Invoice reconciled    │
                                                    │  ✓ Payment posted        │
                                                    └──────────────────────────┘
```

## Payment Flow (Step by Step)

### Phase 1: Till Registration (One-time Setup)

```
DTB Portal             Odoo Admin                    DTB Gateway
    │                      │                              │
    │                      │  Generate Till Number ──────►│
    │                      │◄──── Till: 100004            │
    │                      │                              │
    │                      │  Create Till ───────────────►│
    │                      │  (link to account 5029728002) │
    │                      │◄──── Till Created             │
    │                      │                              │
    │                      │  Authorize Till ────────────►│
    │                      │◄──── Till ACTIVE              │
    │                      │                              │
    │                      │  Set validation_url:          │
    │                      │  https://odoo.example.com    │
    │                      │  /api/dtb/validate-reference  │
    │                      │                              │
    │                      │  Set callback_url:            │
    │                      │  https://odoo.example.com    │
    │                      │  /api/dtb/callback/notification│
```

### Phase 2: Customer Payment

```
M-Pesa User           DTB Gateway              Odoo ERP
    │                      │                       │
    │  Opens M-Pesa        │                       │
    │  Enters Till: 100004 │                       │
    │  Amount: 1,500 KES   │                       │
    │  Ref: INV/2026/001   │                       │
    │                      │                       │
    │──── Paybill Req ────►│                       │
    │                      │                       │
    │                      │──[OPTIONAL]──────────►│
    │                      │  GET /validate-ref    │
    │                      │  ?tillNumber=100004   │
    │                      │  &ref=INV/2026/001    │
    │                      │  &amount=1500         │
    │                      │                       │
    │                      │◄── 200 OK ────────────│
    │                      │  {                    │
    │                      │   value_1: "Patient", │
    │                      │   value_2: "INV/001", │
    │                      │   value_3: "1500.0"   │
    │                      │  }                    │
    │                      │                       │
    │◄── Confirm ─────────│                       │
    │  (PIN prompt)        │                       │
    │                      │                       │
    │──── PIN Entered ────►│                       │
    │                      │                       │
    │◄── Success ─────────│                       │
    │                      │                       │
    │                      │──POST /callback──────►│
    │                      │  {                    │
    │                      │   xref: "EXT-72D0...",│
    │                      │   amount: "1500",     │
    │                      │   narration:          │
    │                      │    "INV/2026/001",    │
    │                      │   customer_name:      │
    │                      │    "John Doe",        │
    │                      │   cbs_reference:      │
    │                      │    "110CDPO172380008" │
    │                      │  }                    │
    │                      │                       │
    │                      │                       │── Create dtb.moja.transaction
    │                      │                       │── Search invoice by narration
    │                      │                       │── Create account.payment
    │                      │                       │── Reconcile
    │                      │                       │── Mark processed
    │                      │                       │
    │                      │◄── 200 OK ────────────│
    │                      │  {ack_code: "00"}     │
    │                      │                       │
```

### Phase 3: Reconciliation (Edge Cases)

```
DTB Gateway                         Odoo ERP
    │                                    │
    │──POST /callback (unmatched)───────►│
    │  {narration: "forgot reference"}   │
    │                                    │
    │                                    │── Create dtb.moja.transaction
    │                                    │── No matching invoice found
    │                                    │── state = 'mismatch'
    │                                    │
    │◄── 200 {ack: "UNMATCHED_REFERENCE}│
    │                                    │
    │                                    │
    │  ┌─────────────────────────────────┴──── Manager Reviews ────┐
    │  │  dtb.moja.transaction:                                    │
    │  │  • xref: EXT-72D0...                                      │
    │  │  • amount: 1,500 KES                                     │
    │  │  • customer: John Doe                                    │
    │  │  • state: mismatch                                        │
    │  │                                                           │
    │  │  [Match to Invoice]  [Mark as Reversed]  [Ignore]         │
    │  └───────────────────────────────────────────────────────────┘
```

---

## Odoo Data Flow

### Models Created

```python
# Till Configuration
dtb.moja.till:
    name               # Branch label
    company_id         # Multi-company isolation
    till_number        # DTB till number (e.g. "100004")
    user_id            # DTB API User ID
    password           # DTB API Password (encrypted)
    api_key            # Bearer token for controller auth
    channel            # "MBS"
    journal_id         # Odoo bank journal for payments
    is_active          # Enable/disable

# Transaction Log
dtb.moja.transaction:
    xref               # DTB unique trace ID (UNIQUE constraint)
    cbs_reference      # Core banking reference
    amount             # Monetary amount
    currency_id        # Default: company currency
    customer_name      # Payer name
    customer_mobile    # Payer phone
    narration          # Invoice reference from customer
    state              # draft → processed | mismatch | reversed
    till_id            # Linked till config
    invoice_id         # Matched invoice (if reconciled)
    error_reason       # Why matching failed
```

### API Endpoints

| Endpoint | Method | Purpose | Called By |
|---|---|---|---|
| `/api/dtb/validate-reference` | GET | Pre-payment invoice validation | DTB Gateway |
| `/api/dtb/callback/notification` | POST | Post-payment settlement notification | DTB Gateway |

---

## Test Scenarios

| # | Scenario | Expected | Test File |
|---|---|---|---|
| 1 | Create till config with all fields | Record saved, defaults set | `test_dtb_till.py` |
| 2 | Till defaults to active/channel=MBS | Correct defaults | `test_dtb_till.py` |
| 3 | Log transaction from callback payload | xref, amount, state=draft | `test_dtb_transaction.py` |
| 4 | Default state is draft | No state provided → draft | `test_dtb_transaction.py` |
| 5 | Duplicate xref raises error | UNIQUE constraint | `test_dtb_transaction.py` |
| 6 | Validate reference matches invoice | Returns 200 with values | `test_dtb_controller.py` |
| 7 | Validate reference not found | Returns None | `test_dtb_controller.py` |
| 8 | Validate reference amount mismatch | Returns None | `test_dtb_controller.py` |
| 9 | Callback creates transaction log | Log created, ack=00 | `test_dtb_controller.py` |
| 10 | Callback idempotency | Duplicate returns success, 1 record | `test_dtb_controller.py` |
| 11 | Callback matches & reconciles invoice | state=processed, invoice linked | `test_dtb_controller.py` |
| 12 | Callback unmatched → mismatch | state=mismatch, ack=UNMATCHED | `test_dtb_controller.py` |

---

## Daraja (M-Pesa API) vs. Till Moja

Safaricom's **Daraja API** is the direct M-Pesa API. **DTB Till Moja** sits on top of it:

| Aspect | Daraja API | DTB Till Moja |
|---|---|---|
| Provider | Safaricom (direct) | DTB Kenya (aggregator) |
| Auth | Consumer Key + Secret → OAuth Token | API Key (Bearer) |
| Till/Paybill | Your own Paybill/Till | DTB-issued Till number |
| Callback | Your server handles it | DTB handles + forwards to you |
| Settlement | Direct to your M-Pesa wallet | To your DTB bank account |
| Reconciliation | Manual | DTB provides structured data |
| Validation | None (M-Pesa accepts any ref) | DTB calls your validation URL |
| Use case | Direct M-Pesa integration | Bank-integrated payments |

### When to use which

- **Use Daraja directly** if: You want funds in M-Pesa wallet, handle callbacks yourself, no bank account needed
- **Use DTB Till Moja** if: You want funds in your bank account, need validation before payment, want structured reconciliation

---

## STK Push (B2C) Flow

While the Till Moja (C2B) flow requires the customer to manually open M-Pesa and pay,
the **STK Push** flow lets Odoo initiate the payment by sending a push notification
to the customer's phone.

### Architecture

```
[Customer Browser]     [Odoo Server]       [DTB Gateway]       [Safaricom M-Pesa]     [Customer Phone]
        |                    |                   |                      |                    |
        |-- 1. Click Pay --->|                   |                      |                    |
        |   Enter Phone      |                   |                      |                    |
        |                    |-- 2. STK Req ---->|                      |                    |
        |                    |   (POST /stk-push)|-- 3. Daraja API ---->|                    |
        |                    |                   |   (STK Push)         |-- 4. Prompt ------>|
        |                    |                   |                      |    (USSD popup)    |
        |                    |                   |                      |                    |
        |                    |                   |                      |<-- 5. Enter PIN ---|
        |                    |                   |<-- 6. Settlement ----|                    |
        |                    |                   |    Notification      |                    |
        |                    |                   |                      |                    |
        |                    |<-- 7. Callback ---|                      |                    |
        |                    |   (Daraja format) |                      |                    |
        |                    |                   |                      |                    |
        |                    | [Reconciles]      |                      |                    |
        |<-- 8. Confirmed --|                   |                      |                    |
```

### Step-by-Step

1. **Customer clicks Pay**: On Odoo checkout/invoice page, customer selects
   "M-Pesa Express", enters phone number, clicks Pay.

2. **Odoo → DTB STK Push**: Odoo sends `POST /till-moja/stk-push` to DTB with:
   ```json
   {
     "request_identifier": { "xref": "EXT-...", "user_id": "API_M247",
       "password": "...", "channel": "MBS" },
     "request_data": {
       "till_number": "100004",
       "amount": "1500",
       "phone_number": "254790999957",
       "narration": "INV/2026/001",
       "callback_url": "https://odoo.example.com/api/dtb/stk-callback"
     }
   }
   ```

3. **DTB forwards to Safaricom**: DTB translates to Daraja STK Push format,
   sends to Safaricom with your till credentials.

4. **Customer gets phone prompt**: Safaricom sends USSD push notification:
   *"Pay KES 1,500 to DTB Merchant XYZ?"*

5. **Customer enters PIN**: On phone keypad.

6. **Safaricom notifies DTB**: Payment settled, DTB core banking credits
   merchant account.

7. **DTB calls Odoo**: Sends `POST /api/dtb/stk-callback` with Daraja format:
   ```json
   {
     "Body": {
       "stkCallback": {
         "CheckoutRequestID": "ws_CO_DMZ_1234567890",
         "ResultCode": 0,
         "ResultDesc": "Success",
         "CallbackMetadata": {
           "Item": [
             {"Name": "Amount", "Value": 1500},
             {"Name": "MpesaReceiptNumber", "Value": "RGH1234567"},
             {"Name": "PhoneNumber", "Value": 254790999957}
           ]
         }
       }
     }
   }
   ```

8. **Odoo reconciles**: Finds the pending_stk transaction by `CheckoutRequestID`,
   creates `account.payment`, reconciles with invoice, updates state to `processed`.

### Odoo Model Changes for STK

| Model | New Fields |
|---|---|
| `dtb.moja.till` | `stk_push_url`, `stk_push_callback_url` |
| `dtb.moja.transaction` | `checkout_request_id`, `phone_number`, `payment_method` (till_moja/stk_push), `stk_response_code`, `stk_result_code`, `stk_result_desc`, `mpesa_receipt` |

### STK Transaction States

```
pending_stk ──► processed  (payment successful, invoice reconciled)
            └──► failed     (customer cancelled, timeout, or error)
            └──► mismatch   (STK succeeded but invoice not found)
```

### API Endpoints Summary

| Endpoint | Method | Direction | Purpose |
|---|---|---|---|
| `/api/dtb/validate-reference` | GET | DTB → Odoo | Pre-payment invoice validation |
| `/api/dtb/callback/notification` | POST | DTB → Odoo | Till Moja C2B payment callback |
| `/api/dtb/stk-callback` | POST | DTB → Odoo | STK Push payment callback (Daraja format) |
| Stk Push (outgoing) | POST | Odoo → DTB | Initiate STK Push (configurable URL) |

### Test Scenarios (STK)

| # | Scenario | Expected | Test File |
|---|---|---|---|
| 1 | Till has STK config fields | stk_push_url stored | `test_dtb_stk.py` |
| 2 | Transaction has STK fields | checkout_request_id, phone stored | `test_dtb_stk.py` |
| 3 | STK Push creates pending transaction | state=pending_stk | `test_dtb_stk.py` |
| 4 | DTB rejects STK Push | UserError raised | `test_dtb_stk.py` |
| 5 | STK callback success (Daraja format) | state=processed, invoice reconciled | `test_dtb_stk.py` |
| 6 | STK callback idempotency | Duplicate handled, 1 record | `test_dtb_stk.py` |
| 7 | STK callback failed payment | state=failed, result_code=1032 | `test_dtb_stk.py` |
| 8 | STK callback unknown checkout_id | ack=TRANSACTION_NOT_FOUND | `test_dtb_stk.py` |
| 9 | STK callback flat format | Also handles non-Daraja format | `test_dtb_stk.py` |

---

## Sandbox Quick Start

```bash
# Terminal 1: Start Odoo (via Docker)
cd /home/wyckie/Desktop/ODOO/POS
docker compose up -d

# Terminal 2: Start mock DTB server
cd custom_addons/mobipine_odoo_dtb_intergration/sandbox
pip install flask requests
python mock_dtb_server.py

# Terminal 3: Run CLI test
python mock_dtb_server.py --cli-test

# Or send a test payment via curl
curl -X POST http://localhost:5050/sandbox/trigger-payment-flow \
  -H "Content-Type: application/json" \
  -d '{
    "till_number": "100004",
    "amount": "1500",
    "narration": "INV/2026/001",
    "customer_name": "Test Patient"
  }'
```
