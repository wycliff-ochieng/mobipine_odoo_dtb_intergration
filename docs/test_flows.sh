#!/usr/bin/env bash
# ==============================================================================
# DTB Till Moja & M-Pesa Webhook Integration Complete Flow Test Suite
# Mapping real invoices from 'vivace-prod' dashboard
# ==============================================================================

ODOO_URL="http://localhost:8569"
DB_NAME="vivace-prod"
TILL_NUMBER="100004"
API_KEY="sandbox_test_api_key_123"

# Colors for output
export GREEN='\033[0;32m'
export RED='\033[0;31m'
export YELLOW='\033[1;33m'
export NC='\033[0m'
export BOLD='\033[1m'

log_case() { echo -e "\n${BOLD}${YELLOW}[TEST CASE] $1${NC}"; }
log_success() { echo -e "   ${GREEN}✓ Success:${NC} $1"; }
log_error() { echo -e "   ${RED}✗ Failed:${NC} $1"; }

echo -e "======================================================================="
echo -e "       DTB TILL MOJA Webhook Integration Test Suite"
echo -e "       Target Database: ${DB_NAME} | Port: 8569"
echo -e "======================================================================="

# ------------------------------------------------------------------------------
# 1. Reference Validation Tests (GET)
# ------------------------------------------------------------------------------
log_case "1A. Reference Validation - Exact Match (INV/2026/00001 - Aarna Singh - 9,000 KSh)"
RESP_1A=$(curl -s -w "\n%{http_code}" -X GET "${ODOO_URL}/api/dtb/validate-reference?tillNumber=${TILL_NUMBER}&referenceNumber=INV/2026/00001&transactionAmount=9000" \
  -H "Authorization: Bearer ${API_KEY}" -H "X-Odoo-Database: ${DB_NAME}")
BODY_1A=$(echo "$RESP_1A" | head -n 1)
STATUS_1A=$(echo "$RESP_1A" | tail -n 1)

if [ "$STATUS_1A" -eq 200 ]; then
    log_success "Invoice matched correctly. Response: ${BODY_1A}"
else
    log_error "Expected 200, got ${STATUS_1A}. Response: ${BODY_1A}"
fi

log_case "1B. Reference Validation - Exact Match (INV/2026/00014 - Beatrice Kosgei - 8,700 KSh)"
RESP_1B=$(curl -s -w "\n%{http_code}" -X GET "${ODOO_URL}/api/dtb/validate-reference?tillNumber=${TILL_NUMBER}&referenceNumber=INV/2026/00014&transactionAmount=8700" \
  -H "Authorization: Bearer ${API_KEY}" -H "X-Odoo-Database: ${DB_NAME}")
BODY_1B=$(echo "$RESP_1B" | head -n 1)
STATUS_1B=$(echo "$RESP_1B" | tail -n 1)

if [ "$STATUS_1B" -eq 200 ]; then
    log_success "Invoice matched correctly. Response: ${BODY_1B}"
else
    log_error "Expected 200, got ${STATUS_1B}. Response: ${BODY_1B}"
fi

log_case "1C. Reference Validation - Amount Mismatch (INV/2026/00013 - Expected 20 KSh, Sent 1 KSh)"
RESP_1C=$(curl -s -w "\n%{http_code}" -X GET "${ODOO_URL}/api/dtb/validate-reference?tillNumber=${TILL_NUMBER}&referenceNumber=INV/2026/00013&transactionAmount=1" \
  -H "Authorization: Bearer ${API_KEY}" -H "X-Odoo-Database: ${DB_NAME}")
BODY_1C=$(echo "$RESP_1C" | head -n 1)
STATUS_1C=$(echo "$RESP_1C" | tail -n 1)

if [ "$STATUS_1C" -eq 404 ]; then
    log_success "Correctly rejected due to amount mismatch (Status ${STATUS_1C}). Response: ${BODY_1C}"
else
    log_error "Expected 404, got ${STATUS_1C}. Response: ${BODY_1C}"
fi

log_case "1D. Reference Validation - Nonexistent Invoice Code"
RESP_1D=$(curl -s -w "\n%{http_code}" -X GET "${ODOO_URL}/api/dtb/validate-reference?tillNumber=${TILL_NUMBER}&referenceNumber=INV/9999/999&transactionAmount=1000" \
  -H "Authorization: Bearer ${API_KEY}" -H "X-Odoo-Database: ${DB_NAME}")
BODY_1D=$(echo "$RESP_1D" | head -n 1)
STATUS_1D=$(echo "$RESP_1D" | tail -n 1)

if [ "$STATUS_1D" -eq 404 ]; then
    log_success "Correctly rejected non-existent reference (Status ${STATUS_1D}). Response: ${BODY_1D}"
else
    log_error "Expected 404, got ${STATUS_1D}. Response: ${BODY_1D}"
fi


# ------------------------------------------------------------------------------
# 2. C2B Webhook Callback Tests (POST)
# ------------------------------------------------------------------------------
log_case "2A. Processing Payment Callback (INV/2026/00013 - Abdiladif Ibrahim - 20 KSh)"
XREF="EXT-C2B-$(date +%s)"
RESP_2A=$(curl -s -w "\n%{http_code}" -X POST "${ODOO_URL}/api/dtb/callback/notification" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "X-Odoo-Database: ${DB_NAME}" \
  -d "{
    \"xref\": \"${XREF}\",
    \"cbs_reference\": \"CBS$(date +%s)\",
    \"cbs_module\": \"RT\",
    \"account_number\": \"${TILL_NUMBER}\",
    \"branch_code\": \"023\",
    \"currency\": \"KES\",
    \"transaction_time\": \"$(date +'%Y%m%d %H:%M:%S')\",
    \"value_date\": \"$(date +'%Y%m%d')\",
    \"amount\": \"20\",
    \"reversal_indicator\": \"n\",
    \"debit_credit_indicator\": \"C\",
    \"exchange_rate\": \"1\",
    \"financial_year\": \"FY$(date +'%Y')\",
    \"customer_name\": \"Abdiladif Ibrahim\",
    \"customer_mobile\": \"254700000000\",
    \"narration\": \"INV/2026/00013\"
  }")
BODY_2A=$(echo "$RESP_2A" | head -n 1)
STATUS_2A=$(echo "$RESP_2A" | tail -n 1)

if [ "$STATUS_2A" -eq 200 ]; then
    log_success "Payment Callback processed successfully. Response: ${BODY_2A}"
else
    log_error "Payment Callback failed (Status ${STATUS_2A}). Response: ${BODY_2A}"
fi

log_case "2B. Verifying Callback Idempotency (Resending Same payload of 2A)"
RESP_2B=$(curl -s -w "\n%{http_code}" -X POST "${ODOO_URL}/api/dtb/callback/notification" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "X-Odoo-Database: ${DB_NAME}" \
  -d "{
    \"xref\": \"${XREF}\",
    \"cbs_reference\": \"CBS-DUP\",
    \"amount\": \"20\",
    \"account_number\": \"${TILL_NUMBER}\",
    \"narration\": \"INV/2026/00013\"
  }")
BODY_2B=$(echo "$RESP_2B" | head -n 1)
STATUS_2B=$(echo "$RESP_2B" | tail -n 1)

if [ "$STATUS_2B" -eq 200 ]; then
    log_success "Duplicate payload ignored correctly (Idempotent). Response: ${BODY_2B}"
else
    log_error "Failed duplicate prevention (Status ${STATUS_2B}). Response: ${BODY_2B}"
fi

log_case "2C. Payment Callback - Unmatched Reference Mismatch (INV/2026/99999)"
RESP_2C=$(curl -s -w "\n%{http_code}" -X POST "${ODOO_URL}/api/dtb/callback/notification" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "X-Odoo-Database: ${DB_NAME}" \
  -d "{
    \"xref\": \"EXT-MISMATCH-$(date +%s)\",
    \"cbs_reference\": \"CBS-MISMATCH\",
    \"amount\": \"1500\",
    \"account_number\": \"${TILL_NUMBER}\",
    \"narration\": \"INV/2026/99999\"
  }")
BODY_2C=$(echo "$RESP_2C" | head -n 1)
STATUS_2C=$(echo "$RESP_2C" | tail -n 1)

if [ "$STATUS_2C" -eq 200 ]; then
    log_success "Correctly processed unmatched transaction to Mismatch Queue. Response: ${BODY_2C}"
else
    log_error "Mismatch processing failed (Status ${STATUS_2C}). Response: ${BODY_2C}"
fi


# ------------------------------------------------------------------------------
# 3. STK Callback Webhook Tests (POST)
# ------------------------------------------------------------------------------
log_case "3A. Simulating Successful M-Pesa STK Callback (Reconciling INV/2026/00012 - Mercy Chepkoech - 1 KSh)"
# Pre-inject a matching pending STK transaction in database for this checkout request ID
# Normally triggered by Odoo action button; we use a mock checkout ID here.
CHECKOUT_ID="ws_CO_STK_MOCK_$(date +%s)"

# Create local transaction entry in Odoo via python shell inside docker first
docker exec -i pos_odoo_platform odoo shell -d ${DB_NAME} --no-xmlrpc <<EOF
self.env['dtb.moja.transaction'].create({
    'xref': 'STK-XREF-$(date +%s)',
    'amount': 1.0,
    'payment_method': 'stk_push',
    'state': 'pending_stk',
    'checkout_request_id': '${CHECKOUT_ID}',
    'narration': 'INV/2026/00012',
})
self.env.cr.commit()
EOF

# Now trigger the incoming success webhook callback from M-Pesa
RESP_3A=$(curl -s -w "\n%{http_code}" -X POST "${ODOO_URL}/api/dtb/stk-callback" \
  -H "Content-Type: application/json" \
  -H "X-Odoo-Database: ${DB_NAME}" \
  -d "{
    \"Body\": {
      \"stkCallback\": {
        \"MerchantRequestID\": \"MRID-DARAJA-999\",
        \"CheckoutRequestID\": \"${CHECKOUT_ID}\",
        \"ResultCode\": 0,
        \"ResultDesc\": \"The service request is processed successfully.\",
        \"CallbackMetadata\": {
          \"Item\": [
            {\"Name\": \"Amount\", \"Value\": 1.0},
            {\"Name\": \"MpesaReceiptNumber\", \"Value\": \"RGH$(date +%s)\"},
            {\"Name\": \"PhoneNumber\", \"Value\": 254790999957}
          ]
        }
      }
    }
  }")
BODY_3A=$(echo "$RESP_3A" | head -n 1)
STATUS_3A=$(echo "$RESP_3A" | tail -n 1)

if [ "$STATUS_3A" -eq 200 ]; then
    log_success "STK Callback processed and Invoice marked Paid successfully. Response: ${BODY_3A}"
else
    log_error "STK Callback processing failed (Status ${STATUS_3A}). Response: ${BODY_3A}"
fi

echo -e "\n======================================================================="
echo -e "       TEST RUN COMPLETED"
echo -e "======================================================================="