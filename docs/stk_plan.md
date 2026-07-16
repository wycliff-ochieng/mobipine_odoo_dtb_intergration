# STK 2-Way Settlement Plan

## Objective
Enable STK Push payments to settle via **two modes**:
1. **Till Moja** — funds settle to the Till Moja balance (existing)
2. **Core Banking** — funds settle directly to the merchant's bank account

The settlement destination is determined by the till configuration on DTB's side
(`account_source` / `account_id` in CreateTill).  Odoo must track which mode a
till uses and adapt callback processing accordingly.

---

## API Endpoints

### `GET /api/dtb/validate-reference`
- **Purpose**: DTB queries Odoo to validate an invoice reference before settlement.
- **Dual route**: query-string params OR path params.
  - Query: `GET /api/dtb/validate-reference?tillNumber=100004&referenceNumber=INV/001&transactionAmount=1500`
  - Path:  `GET /api/dtb/validate-reference/100004/INV/001/1500`
- **Headers logged**: Full incoming HTTP headers captured at method entry.
- **Auth**: `Authorization: Bearer <api_key>` — matched against `dtb.moja.till.api_key`.
- **Response (200)**: `{"till_number", "reference_id", "value_1".."value_5"}`
- **Response (404)**: Reference not found or amount mismatch.

### `POST /api/dtb/callback/notification`
- **Purpose**: DTB notifies Odoo of a completed Till Moja C2B payment.
- **Headers + body logged**: Full raw headers + raw body captured at method entry.
- **Settlement-aware**: Looks up till by `account_number` (till_number or bank
  account_id). Uses `settlement_mode` from till to choose invoice matching strategy:
  - **till_moja**: match by `narration` (invoice payment_reference).
  - **core_banking**: try `cbs_reference` first, then `narration`.
- **Response (200)**: `{"xref", "user_reference", "ack_code": "00", "ack_description"}`

### `POST /api/dtb/stk-callback`
- **Purpose**: DTB/Safaricom sends STK Push result.
- **Headers + body logged**: Full raw headers + raw body captured at method entry.
- **Settlement-aware**: Reads `dtb_settlement_mode` from transaction.
  For `core_banking`, tries `provider_reference` as an invoice match key.

---

## Efficient Logging Strategy

Logging uses two layers that work together:

### Layer 1: DTBLogger (structured events)
```python
log = DTBLogger('COMPONENT')
log.incoming('WEBHOOK', xref=xref, amount=amount)
log.ok('PROCESSED', tx_id=tx.id)
log.warn('MISMATCH', reason='no invoice found')
log.exc('EXCEPTION')  # includes full traceback
```
- Prefixed ASCII markers: `[IN]`, `[OK]`, `[WARN]`, `[EXC]`, `[TIME]`
- Values truncated at 500 chars to avoid log bloat
- Timed context manager for HTTP calls: `with log.timed('HTTP_POST')`
- Used for event-level tracing throughout models and controllers

### Layer 2: Raw `_logger` (diagnostic dumps)
```python
_logger.info('[DTB][HEADERS] validate_reference | Incoming Headers:\n%s',
             json.dumps(dict(request.httprequest.headers.items()), indent=4))
_logger.info('[DTB][BODY] payment_callback | Raw Body:\n%s',
             request.httprequest.data.decode('utf-8', errors='replace'))
```
- Only at controller entry (before any processing)
- Captures raw HTTP headers + request body verbatim
- Tagged with `[DTB][HEADERS]` / `[DTB][BODY]` for easy `grep`
- Can be disabled after initial DTB integration validation

### Filtering logs
```bash
docker logs -f pos_odoo_platform | grep "\[DTB\]\[HEADERS\]"
docker logs -f pos_odoo_platform | grep "\[DTB\]\["
docker logs -f pos_odoo_platform | grep "\[WARN\]\|\[ERR\]\|\[EXC\]"
```

---

## Changes

### 1. Model — `dtb.moja.till`
Add settlement configuration fields:

| Field | Type | Purpose |
|---|---|---|
| `settlement_mode` | selection (`till_moja`, `core_banking`) | Which settlement mode this till uses |
| `account_source` | Char | `CORE BANKING` or empty (for till balance) |
| `account_id` | Char | Bank account number when mode is core_banking |

### 2. Model — `dtb.moja.transaction`
Add settlement tracking field:

| Field | Type | Purpose |
|---|---|---|
| `settlement_mode` | selection (same as till) | Record how this tx was settled |

### 3. Model — `payment.transaction` (inherit)
Add settlement tracking field:

| Field | Type | Purpose |
|---|---|---|
| `dtb_settlement_mode` | selection | Record settlement mode on payment tx |

### 4. View — `dtb_till_views.xml`
Add settlement mode group below "STK Push Settings":
- `settlement_mode` radio button
- `account_source` (visible when core_banking)
- `account_id` (visible when core_banking)
- Uses Odoo 17+ `invisible` attribute (NOT deprecated `attrs`)

### 5. View — `dtb_transaction_views.xml`
Add `dtb_settlement_mode` to the DTB Details notebook page.

### 6. View — `dtb_stk_wizard_views.xml`
Add `settlement_mode` field so the user can choose where funds go.

### 7. Wizard — `dtb.stk.payment.wizard`
- Add `settlement_mode` selection field (default from till via onchange)
- Add `till_id` field to let user pick which till (and thus which mode)
- Pass settlement_mode to `_stk_push_request`

### 8. Validation — `dtb.moja.validation`
- `_stk_push_request`: accept `settlement_mode` param, store on tx
- `_process_callback_payload`: handle core_banking callbacks by matching
  `cbs_reference` and `account_number`; look up till by bank `account_id`
- `_process_stk_callback`: use settlement_mode from tx to determine
  reconciliation path (try `provider_reference` for core_banking matches)

### 9. Controller — `controllers/main.py`
- Dual route pattern for validate-reference (query + path params)
- Header + body logging at each endpoint entry
- `sudo()` on model calls for auth-none routes
- Proper HTTP status codes (400, 401, 404, 500)

### 10. Payment Transaction — `models/payment_transaction.py`
- Auto-create `payment.provider` with code `'dtb'` if missing
- Fallback to any available `payment.method` if `DTB_ACQ` not found
- Auto-create "Unreconciled DTB Customer" partner if `partner_id` is falsy
  (prevents PostgreSQL `NOT NULL` violation)
- `dtb_settlement_mode` included in `dtb_fields` passthrough list

---

## Flow Diagrams

### Till Moja Settlement (existing)
```
Odoo STK Push → DTB Gateway → Safaricom → Customer Phone
                                                  ↓
Odoo ← DTB Callback ← DTB Settlement ← Customer enters PIN
       ↑
   Match by narration → Find invoice → Reconcile
```

### Core Banking Settlement (new)
```
Odoo STK Push → DTB Gateway → Safaricom → Customer Phone
                                                  ↓
Odoo ← DTB Callback ← DTB credits bank acct ← Customer enters PIN
       ↑
   Match by cbs_reference/account_number → Find invoice → Reconcile
```

---

## Test Plan

### Test file: `tests/test_stk_2way.py`

#### Class `TestSettlementModeTill`
| Test | What it verifies |
|---|---|
| `test_till_defaults_to_till_moja` | New till defaults to `settlement_mode='till_moja'` |
| `test_till_core_banking_with_account` | Till accepts `core_banking` + `account_id` |
| `test_transaction_stores_settlement_mode` | `dtb.moja.transaction` stores settlement_mode |
| `test_payment_transaction_stores_dtb_settlement_mode` | `payment.transaction` stores `dtb_settlement_mode` |

#### Class `TestC2BCallbackCoreBanking`
| Test | What it verifies |
|---|---|
| `test_callback_lookup_till_by_account_id` | Account number maps to till via `account_id` for core_banking |
| `test_callback_matches_invoice_by_cbs_reference` | Core banking callback matches invoice by `cbs_reference` |
| `test_callback_unmatched_cbs_goes_to_mismatch` | Missing invoice still returns UNMATCHED_REFERENCE |

#### Class `TestStkPushSettlementMode`
| Test | What it verifies |
|---|---|
| `test_stk_push_stores_settlement_mode_from_param` | Explicit settlement_mode param stored on payment tx |
| `test_stk_push_defaults_settlement_from_till` | Defaults to till's settlement_mode when param absent |

#### Class `TestStkCallbackCoreBanking`
| Test | What it verifies |
|---|---|
| `test_stk_callback_core_banking_matches_by_provider_reference` | Core banking STK callback matches invoice via `provider_reference` |

#### Class `TestAutoCreateProvider`
| Test | What it verifies |
|---|---|
| `test_dtb_create_transaction_auto_creates_provider` | Auto-creates `payment.provider` with code `'dtb'` when missing |
| `test_dtb_create_transaction_fallback_partner` | Creates "Unreconciled DTB Customer" partner when no partner_id |
| `test_dtb_create_transaction_fallback_currency` | Falls back to company currency or KES |

### Running tests
```bash
odoo -d <db> --test-enable --test-tags=mobipine_odoo_dtb_intergration --stop-after-init
```

---

## Implementation Order
1. Update `dtb_till.py` — add settlement fields
2. Update `dtb_transaction.py` — add settlement_mode field
3. Update `payment_transaction.py` — add dtb_settlement_mode
4. Update `dtb_till_views.xml` — show settlement fields
5. Update `dtb_transaction_views.xml` — show dtb_settlement_mode
6. Update `dtb_stk_wizard.py` — add settlement_mode and till selection
7. Update `dtb_stk_wizard_views.xml` — show settlement fields
8. Update `dtb_validation.py` — pass settlement_mode, handle both modes
9. Update `controllers/main.py` — dual routes, header logging
10. Update `tests/__init__.py` — register new test file
11. Create `tests/test_stk_2way.py` — 11 test methods across 5 classes
