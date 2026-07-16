# DTB Till Moja — Odoo Module Setup Guide

## Prerequisites

- Odoo 19.0 (Community or Enterprise)
- Python 3.12+
- PostgreSQL 16
- Docker & Docker Compose (for sandbox testing)
- DTB Till Moja API credentials (from DTB Kenya)

---

## 1. Required Credentials from DTB Kenya

Contact DTB Kenya API Team: **support@dtbafrica.com**

You need the following before configuring the module:

| Credential | Description | Example |
|---|---|---|
| **API User ID** | User ID assigned to your API consumer account | `API_M247` |
| **API Password** | Password for API authentication | `qOw1EaF23xvf=` |
| **API Key** | Bearer token for Authorization header | `sk_live_...` |
| **Channel** | Channel code (usually `MBS`) | `MBS` |
| **Till Number(s)** | Registered till number(s) for receiving payments | `100004` |
| **Account Number** | Core bank account linked to the till | `5029728002` |
| **Branch Code** | 3-digit branch code | `023` |

### DTB Onboarding Process

1. Request API access from DTB Kenya (`support@dtbafrica.com`)
2. Receive your **User ID**, **Password**, and **API Key**
3. Use `GET /till-moja/generate-till` to generate a till number
4. Use `POST /till-moja/create-till` to register the till against your bank account
5. Use `POST /till-moja/authorize-till` to activate the till
6. Configure the `validation_url` to point at your Odoo instance
7. Provide the `callback_url` for payment notifications

---

## 2. Odoo Module Configuration

### 2.1 Install the Module

```bash
# Via Docker (production setup)
docker exec pos_odoo_platform odoo server \
  -d postgres \
  -i mobipine_odoo_dtb_intergration \
  --stop-after-init \
  --http-port=8069
```

### 2.2 Configure a Till

1. Navigate to **Accounting → Configuration → DTB Moja → Till Configuration**
2. Click **Create**
3. Fill in:
   - **Name**: Human-readable label (e.g. `Parklands Branch Till`)
   - **Company**: Your Odoo company (multi-company supported)
   - **Till Number**: The DTB till number (e.g. `100004`)
   - **API User ID**: From DTB
   - **API Password**: From DTB
   - **API Key**: From DTB (for controller authorization)
   - **Channel**: `MBS`
   - **Journal**: The Odoo bank journal to post payments to
   - **Active**: Keep checked

### 2.3 STK Push Configuration

If using STK Push (M-Pesa Express), also fill in these on the till form:

- **STK Push URL**: DTB's endpoint for initiating STK Push (default: `https://api.dtbafrica.com/till-moja/stk-push`)
- **STK Callback URL**: Your Odoo public URL where DTB sends STK results (`https://your-odoo.com/api/dtb/stk-callback`)

### 2.4 Webhook URL Configuration

Provide these URLs to DTB during onboarding:

| Purpose | URL | Method |
|---|---|---|
| **Reference Validation** | `https://your-odoo-instance.com/api/dtb/validate-reference` | GET |
| **Payment Callback (C2B)** | `https://your-odoo-instance.com/api/dtb/callback/notification` | POST |
| **STK Callback (B2C)** | `https://your-odoo-instance.com/api/dtb/stk-callback` | POST |

---

## 3. Running Tests

### 3.1 With Docker (CI-style)

```bash
# Build and run tests for this module
docker run --rm --network=host \
  -v "$PWD/custom_addons:/mnt/custom-addons" \
  odoo:19.0 \
  odoo server -d postgres \
    --db_host=localhost \
    --db_user=odoo \
    --db_password=odoo \
    --addons-path=/mnt/custom-addons,/usr/lib/python3/dist-packages/odoo/addons \
    -i mobipine_odoo_dtb_intergration \
    --test-tags ":mobipine_odoo_dtb_intergration" \
    --stop-after-init \
    --http-port=18069
```

### 3.2 Specific Test Class

```bash
docker exec pos_odoo_platform odoo server \
  -d postgres \
  -u mobipine_odoo_dtb_intergration \
  --test-tags ":TestDtbTillConfig" \
  --stop-after-init \
  --http-port=8069
```

### 3.3 Run All Tests

```bash
./run_tests.sh
```

---

## 4. Sandbox Testing

### 4.1 Start the Mock DTB Server

```bash
cd sandbox
pip install flask requests
python mock_dtb_server.py
```

This starts a mock DTB API on `http://localhost:5050`.

### 4.2 Run the CLI Test

```bash
# Set your Odoo URL (default: http://localhost:8569)
export ODOO_BASE_URL=http://localhost:8069
export DTB_API_KEY=sandbox_test_api_key_123

python mock_dtb_server.py --cli-test
```

### 4.3 Send a Test Payment via API

```bash
# Simulate a customer paying via M-Pesa
curl -X POST http://localhost:5050/sandbox/send-payment \
  -H "Content-Type: application/json" \
  -d '{
    "till_number": "100004",
    "amount": "1500",
    "customer_name": "John Doe",
    "customer_mobile": "254700000000",
    "narration": "INV/2026/001",
    "account_number": "0012870005"
  }'
```

### 4.4 Full Payment Flow

```bash
curl -X POST http://localhost:5050/sandbox/trigger-payment-flow \
  -H "Content-Type: application/json" \
  -d '{
    "till_number": "100004",
    "amount": "1500",
    "narration": "INV/2026/001",
    "customer_name": "Test Patient",
    "customer_mobile": "254700000000"
  }'
```

### 4.5 STK Push Simulation

```bash
# Simulate Odoo sending an STK Push + DTB forwarding callback to Odoo
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
    "narration": "INV/STK/001",
    "callback_url": "http://localhost:8069/api/dtb/stk-callback",
    "auto_callback": true
  }'
```

### 4.6 Full STK Flow (End-to-End)

```bash
# Simulates the complete STK flow:
# Creates a till → Sends Daraja-style callback to Odoo
curl -X POST http://localhost:5050/sandbox/simulate-stk-flow \
  -H "Content-Type: application/json" \
  -d '{
    "till_number": "100004",
    "amount": "1500",
    "phone_number": "254790999957",
    "narration": "INV/STK/001",
    "callback_url": "http://localhost:8069/api/dtb/stk-callback"
  }'
```

### 4.7 Reset Sandbox

```bash
curl -X POST http://localhost:5050/sandbox/reset
```

---

## 5. Security Checklist

- [ ] Restrict `/api/dtb/` endpoints to DTB IP addresses only (firewall/nginx)
- [ ] Enforce HTTPS (TLS 1.2+) in production
- [ ] Store `password` and `api_key` securely — Odoo encrypts `fields.Char(password=True)` fields
- [ ] Rotate API keys periodically
- [ ] Monitor `dtb.moja.transaction` for `mismatch` state records
- [ ] Set up alerts for failed reconciliation

---

## 6. Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `401 Unauthorized` from DTB | Credentials wrong or expired | Check user_id/password in till config |
| `409 Conflict` on callback | Duplicate `xref` | Normal — DTB retried, Odoo handled it |
| Transaction stuck in `mismatch` | `narration` didn't match any invoice | Manually reconcile via Transaction Log |
| `Odoo Unreachable` from sandbox | Odoo not running or wrong URL | Check `ODOO_BASE_URL` env var |
| Test payment not creating invoice | Invoice not posted or wrong `payment_reference` | Ensure invoice has matching `payment_reference` and is `posted` |
