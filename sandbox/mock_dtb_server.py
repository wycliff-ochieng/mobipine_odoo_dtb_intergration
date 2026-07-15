"""
DTB Till Moja Mock Server — Sandbox for local Odoo integration testing.

Simulates the Diamond Trust Bank Till Moja API platform so you can
test the Odoo module end-to-end without a real DTB account.

Supports both Till Moja (C2B) and STK Push (B2C) flows.

Usage:
    pip install flask requests
    python mock_dtb_server.py

Then configure Odoo's DTB Till Moja provider to point at:
    http://localhost:5050

The test harness also sends simulated payment callbacks to your
Odoo instance, so configure ODOO_BASE_URL below.
"""

import os
import uuid
import json
import math
import threading
import time
from datetime import datetime

import requests
from flask import Flask, request, jsonify

# ============================================================
# CONFIGURATION — set these before running
# ============================================================
ODOO_BASE_URL = os.environ.get('ODOO_BASE_URL', 'http://localhost:8569')
API_KEY = os.environ.get('DTB_API_KEY', 'sandbox_test_api_key_123')
HOST = os.environ.get('DTB_SANDBOX_HOST', '0.0.0.0')
PORT = int(os.environ.get('DTB_SANDBOX_PORT', 5050))

app = Flask(__name__)

# ============================================================
# In-memory store simulating DTB's database
# ============================================================
till_store = {}          # till_number -> till_data
transaction_store = {}   # xref -> transaction_data
stk_pending = {}         # checkout_request_id -> stk_data
till_counter = [100000]  # auto-increment till seed
stk_counter = [1000]     # auto-increment checkout ID seed


def _check_auth(headers):
    auth = headers.get('Authorization', '')
    return auth == f'Bearer {API_KEY}' or auth == API_KEY


def _generate_xref():
    return f"EXT-{uuid.uuid4().hex[:8].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:12].upper()}"


def _make_response(response_code="000", description="SUCCESS", extra=None):
    resp = {
        "response_data": {
            "trace_id": f"EXT-{uuid.uuid4().hex[:8].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:12].upper()}",
            "response_code": response_code,
            "response_description": description,
        }
    }
    if extra:
        resp["response_data"].update(extra)
    return jsonify(resp)


# ============================================================
# INTERNAL SERVICES — Till Management
# ============================================================

@app.route('/till-moja/generate-till', methods=['GET'])
def generate_till():
    if not _check_auth(request.headers):
        return jsonify({"error": "Unauthorized"}), 401
    till_counter[0] += 1
    return _make_response(extra={"till_number": till_counter[0]})


@app.route('/till-moja/create-till', methods=['POST'])
def create_till():
    if not _check_auth(request.headers):
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    req_data = data.get('request_data', {})
    req_id = data.get('request_identifier', {})

    till_number = req_data.get('till_number', str(till_counter[0] + 1))
    till_counter[0] = max(till_counter[0], int(till_number))

    if till_number in till_store:
        return jsonify({"error": "Duplicate Till"}), 409

    till_store[till_number] = {
        'till_number': till_number,
        'till_name': req_data.get('till_name', 'Sandbox Till'),
        'till_mobile_number': req_data.get('till_mobile_number', '254700000000'),
        'till_email_adress': req_data.get('till_email_adress', 'sandbox@test.io'),
        'account_source': req_data.get('account_source', 'CORE BANKING'),
        'account_id': req_data.get('account_id', '5029728000'),
        'status': 'PENDING',
        'created_at': datetime.now().isoformat(),
    }

    resp = {
        "response_identifier": {
            "xref": req_id.get('xref', _generate_xref()),
            "user_id": req_id.get('user_id', 'SANDBOX'),
            "channel": req_id.get('channel', 'MBS'),
        },
        "response_data": {
            "trace_id": f"EXT-{uuid.uuid4().hex[:8].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:12].upper()}",
            "response_code": "000",
            "response_description": "SUCCESS",
            "till_number": till_number,
        }
    }
    return jsonify(resp)


@app.route('/till-moja/authorize-till', methods=['POST'])
def authorize_till():
    if not _check_auth(request.headers):
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    req_data = data.get('request_data', {})
    req_id = data.get('request_identifier', {})
    till_number = req_data.get('till_number')

    if till_number not in till_store:
        return jsonify({"error": "Till not found"}), 404

    till_store[till_number]['status'] = req_data.get('actor_action', 'APPROVED')

    return jsonify({
        "response_identifier": {
            "xref": req_id.get('xref', _generate_xref()),
            "user_id": req_id.get('user_id', 'SANDBOX'),
            "channel": req_id.get('channel', 'MBS'),
        },
        "response_data": {
            "trace_id": f"EXT-{uuid.uuid4().hex[:8].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:12].upper()}",
            "response_code": "000",
            "response_description": "SUCCESS",
            "till_number": till_number,
        }
    })


@app.route('/till-moja/query-till/<tillNumber>', methods=['GET'])
def query_till(tillNumber):
    if not _check_auth(request.headers):
        return jsonify({"error": "Unauthorized"}), 401
    till = till_store.get(tillNumber)
    if not till:
        return jsonify({"error": "Till not found"}), 404
    return _make_response(extra={"till_data": till})


@app.route('/till-moja/update-till', methods=['PUT'])
def update_till():
    if not _check_auth(request.headers):
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    req_data = data.get('request_data', {})
    till_number = req_data.get('till_number')

    if till_number not in till_store:
        return jsonify({"error": "Till not found"}), 404

    for key in ('till_name', 'till_mobile_number', 'till_email_adress',
                'account_source', 'account_id', 'validation_required',
                'validation_mode'):
        if key in req_data:
            till_store[till_number][key] = req_data[key]

    return _make_response(extra={"till_number": till_number})


@app.route('/till-moja/delete-till/<userId>/<tillNumber>', methods=['DELETE'])
def delete_till(userId, tillNumber):
    if not _check_auth(request.headers):
        return jsonify({"error": "Unauthorized"}), 401
    if tillNumber not in till_store:
        return jsonify({"error": "Till not found"}), 404
    del till_store[tillNumber]
    return _make_response(extra={"till_number": tillNumber})


@app.route('/till-moja/enable-disable-till/<userId>/<tillNumber>/<tillStatus>', methods=['GET'])
def enable_disable_till(userId, tillNumber, tillStatus):
    if not _check_auth(request.headers):
        return jsonify({"error": "Unauthorized"}), 401
    if tillNumber not in till_store:
        return jsonify({"error": "Till not found"}), 404
    till_store[tillNumber]['status'] = tillStatus
    return _make_response(extra={"till_number": tillNumber})


@app.route('/till-moja/query-reference/<tillNumber>/<path:referenceNumber>', methods=['GET'])
def query_reference(tillNumber, referenceNumber):
    if not _check_auth(request.headers):
        return jsonify({"error": "Unauthorized"}), 401
    return _make_response(extra={"till_data": {}})


# ============================================================
# STK PUSH ENDPOINT — Called by Odoo to initiate STK Push
# ============================================================

@app.route('/till-moja/stk-push', methods=['POST'])
def stk_push():
    """
    Simulates DTB's STK Push endpoint.

    Expected payload:
    {
        "request_identifier": { xref, user_id, password, channel },
        "request_data": {
            till_number, amount, phone_number, narration, callback_url
        }
    }
    """
    if not _check_auth(request.headers):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    req_data = data.get('request_data', {})
    req_id = data.get('request_identifier', {})

    till_number = req_data.get('till_number')
    phone_number = req_data.get('phone_number')

    if not till_number or not phone_number:
        return jsonify({"error": "Missing till_number or phone_number"}), 400

    # Generate a checkout request ID
    stk_counter[0] += 1
    checkout_id = f"ws_CO_SANDBOX_{stk_counter[0]}_{uuid.uuid4().hex[:6].upper()}"

    # Store pending STK for callback reference
    stk_pending[checkout_id] = {
        'till_number': till_number,
        'amount': req_data.get('amount', '0'),
        'phone_number': phone_number,
        'narration': req_data.get('narration', ''),
        'callback_url': req_data.get('callback_url', ''),
        'created_at': datetime.now().isoformat(),
        'status': 'PENDING',
    }

    _log(f"STK Push initiated: checkout_id={checkout_id} amount={req_data.get('amount')} "
         f"phone={phone_number} narration={req_data.get('narration')}")

    resp = {
        "response_data": {
            "trace_id": f"EXT-{uuid.uuid4().hex[:8].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:12].upper()}",
            "response_code": "000",
            "response_description": "SUCCESS",
            "checkout_request_id": checkout_id,
        }
    }
    return jsonify(resp)


# ============================================================
# EXTERNAL SERVICES — These call Odoo
# ============================================================

@app.route('/till-moja/query-external-reference/<tillNumber>/<path:referenceNumber>', methods=['GET'])
def query_external_reference(tillNumber, referenceNumber):
    """
    Simulates DTB calling Odoo's reference validation endpoint.
    Proxies to the real Odoo instance.
    """
    amount = request.args.get('transactionAmount', '0')
    try:
        resp = requests.get(
            f"{ODOO_BASE_URL}/api/dtb/validate-reference",
            params={
                'tillNumber': tillNumber,
                'referenceNumber': referenceNumber,
                'transactionAmount': amount,
            },
            headers={'Authorization': f'Bearer {API_KEY}'},
            timeout=10,
        )
        return jsonify(resp.json()), resp.status_code
    except requests.ConnectionError:
        return jsonify({
            "till_number": tillNumber,
            "reference_id": referenceNumber,
            "value_1": "Odoo Unreachable",
            "value_2": "MOCK",
            "value_3": amount,
            "value_4": "",
            "value_5": "",
        }), 200


# ============================================================
# TEST HARNESS — Till Moja C2B Payment Flow
# ============================================================

@app.route('/sandbox/send-payment', methods=['POST'])
def send_test_payment():
    """
    Simulates a customer paying via M-Pesa Paybill (C2B) and DTB sending
    the payment callback to Odoo's /api/dtb/callback/notification.

    POST /sandbox/send-payment
    {
        "till_number": "100004",
        "amount": "1500",
        "customer_name": "John Doe",
        "customer_mobile": "254700000000",
        "narration": "INV/2026/001",
        "account_number": "0012870005"
    }
    """
    data = request.get_json(silent=True) or {}
    xref = _generate_xref()

    callback_payload = {
        "xref": xref,
        "cbs_reference": f"CBS{uuid.uuid4().hex[:10].upper()}",
        "cbs_module": "RT",
        "account_number": data.get('account_number', '0012870005'),
        "branch_code": "023",
        "currency": "KES",
        "transaction_time": datetime.now().strftime("%Y%m%d %H:%M:%S"),
        "value_date": datetime.now().strftime("%Y%m%d"),
        "amount": str(data.get('amount', '1500')),
        "reversal_indicator": "n",
        "debit_credit_indicator": "C",
        "exchange_rate": "1",
        "financial_year": f"FY{datetime.now().year}",
        "customer_name": data.get('customer_name', 'John Doe'),
        "customer_mobile": data.get('customer_mobile', '254700000000'),
        "narration": data.get('narration', 'INV/2026/001'),
    }

    return _send_to_odoo('callback/notification', callback_payload)


@app.route('/sandbox/trigger-payment-flow', methods=['POST'])
def trigger_payment_flow():
    """
    Full end-to-end C2B simulation:
    1. Creates a till (if not exists)
    2. Sends a payment callback to Odoo

    POST /sandbox/trigger-payment-flow
    {
        "till_number": "100004",
        "amount": "1500",
        "narration": "INV/2026/001",
        "customer_name": "John Doe",
        "customer_mobile": "254700000000"
    }
    """
    data = request.get_json(silent=True) or {}
    till_number = data.get('till_number', '100004')

    if till_number not in till_store:
        till_store[till_number] = {
            'till_number': till_number,
            'till_name': f'Till {till_number}',
            'status': 'ACTIVE',
            'created_at': datetime.now().isoformat(),
        }

    xref = _generate_xref()
    callback_payload = {
        "xref": xref,
        "cbs_reference": f"CBS{uuid.uuid4().hex[:10].upper()}",
        "cbs_module": "RT",
        "account_number": till_number,
        "branch_code": "023",
        "currency": "KES",
        "transaction_time": datetime.now().strftime("%Y%m%d %H:%M:%S"),
        "value_date": datetime.now().strftime("%Y%m%d"),
        "amount": str(data.get('amount', '1500')),
        "reversal_indicator": "n",
        "debit_credit_indicator": "C",
        "exchange_rate": "1",
        "financial_year": f"FY{datetime.now().year}",
        "customer_name": data.get('customer_name', 'John Doe'),
        "customer_mobile": data.get('customer_mobile', '254700000000'),
        "narration": data.get('narration', 'INV/2026/001'),
    }

    return _send_to_odoo('callback/notification', callback_payload)


# ============================================================
# TEST HARNESS — STK Push (B2C) Flow
# ============================================================

@app.route('/sandbox/send-stk-push', methods=['POST'])
def send_test_stk_push():
    """
    Simulates Odoo sending an STK Push to DTB.
    Mocks the DTB STK Push endpoint and optionally sends a
    callback to Odoo's /api/dtb/stk-callback.

    POST /sandbox/send-stk-push
    {
        "till": { "till_number": "100004", "user_id": "API_M247", "password": "..." },
        "amount": "1500",
        "phone_number": "254790999957",
        "narration": "INV/STK/001",
        "callback_url": "http://localhost:8069/api/dtb/stk-callback",
        "auto_callback": true
    }

    If auto_callback is true, the sandbox automatically sends a
    Daraja-style STK callback to Odoo (simulating the customer paying).
    """
    data = request.get_json(silent=True) or {}
    till_info = data.get('till', {})
    till_number = till_info.get('till_number', '100004')
    amount = str(data.get('amount', '1500'))
    phone = data.get('phone_number', '254790999957')
    narration = data.get('narration', 'INV/STK/001')
    callback_url = data.get('callback_url', f'{ODOO_BASE_URL}/api/dtb/stk-callback')
    auto_callback = data.get('auto_callback', True)

    # Ensure till exists
    if till_number not in till_store:
        till_store[till_number] = {
            'till_number': till_number,
            'till_name': f'Till {till_number}',
            'status': 'ACTIVE',
        }

    # Generate checkout ID (simulating DTB -> Safaricom)
    stk_counter[0] += 1
    checkout_id = f"ws_CO_SIM_{stk_counter[0]}_{uuid.uuid4().hex[:6].upper()}"

    stk_pending[checkout_id] = {
        'till_number': till_number,
        'amount': amount,
        'phone_number': phone,
        'narration': narration,
        'callback_url': callback_url,
        'status': 'PENDING',
    }

    # If auto_callback, send a Daraja-style callback to Odoo after a short delay
    if auto_callback:
        mpesa_receipt = f"RGH{uuid.uuid4().hex[:7].upper()}"

        def delayed_callback():
            time.sleep(1)
            _log(f"Sending STK callback for checkout_id={checkout_id}")
            callback_payload = {
                "Body": {
                    "stkCallback": {
                        "MerchantRequestID": f"MRID_{uuid.uuid4().hex[:8].upper()}",
                        "CheckoutRequestID": checkout_id,
                        "ResultCode": 0,
                        "ResultDesc": "The service request is processed successfully.",
                        "CallbackMetadata": {
                            "Item": [
                                {"Name": "Amount", "Value": float(amount)},
                                {"Name": "MpesaReceiptNumber", "Value": mpesa_receipt},
                                {"Name": "PhoneNumber", "Value": int(phone)},
                            ]
                        }
                    }
                }
            }
            try:
                resp = requests.post(callback_url, json=callback_payload,
                                     headers={'Authorization': f'Bearer {API_KEY}'},
                                     timeout=10)
                _log(f"STK callback response: {resp.status_code} {resp.text}")
                stk_pending[checkout_id]['status'] = 'CALLBACK_SENT'
            except requests.ConnectionError:
                _log(f"STK callback failed — Odoo unreachable at {callback_url}")
                stk_pending[checkout_id]['status'] = 'CALLBACK_FAILED'

        thread = threading.Thread(target=delayed_callback)
        thread.daemon = True
        thread.start()

    result = {
        "status": "stk_push_sent",
        "checkout_request_id": checkout_id,
        "amount": amount,
        "phone_number": phone,
        "narration": narration,
        "auto_callback": auto_callback,
    }
    return jsonify(result), 200


@app.route('/sandbox/simulate-stk-flow', methods=['POST'])
def simulate_stk_flow():
    """
    Full end-to-end STK flow simulation.
    1. Creates a till (if not exists)
    2. Sends STK Push to DTB (simulated)
    3. Sends Daraja-style callback to Odoo

    POST /sandbox/simulate-stk-flow
    {
        "till_number": "100004",
        "amount": "1500",
        "phone_number": "254790999957",
        "narration": "INV/STK/001",
        "callback_url": "http://localhost:8069/api/dtb/stk-callback"
    }
    """
    data = request.get_json(silent=True) or {}
    till_number = data.get('till_number', '100004')
    amount = str(data.get('amount', '1500'))
    phone = data.get('phone_number', '254790999957')
    narration = data.get('narration', 'INV/STK/001')
    callback_url = data.get('callback_url', f'{ODOO_BASE_URL}/api/dtb/stk-callback')

    if till_number not in till_store:
        till_store[till_number] = {
            'till_number': till_number,
            'till_name': f'Till {till_number}',
            'status': 'ACTIVE',
        }

    stk_counter[0] += 1
    checkout_id = f"ws_CO_FLOW_{stk_counter[0]}_{uuid.uuid4().hex[:6].upper()}"
    mpesa_receipt = f"RGH{uuid.uuid4().hex[:7].upper()}"

    def send_callback():
        time.sleep(1)
        daraja_payload = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": f"MRID_{uuid.uuid4().hex[:8].upper()}",
                    "CheckoutRequestID": checkout_id,
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": float(amount)},
                            {"Name": "MpesaReceiptNumber", "Value": mpesa_receipt},
                            {"Name": "PhoneNumber", "Value": int(phone)},
                        ]
                    }
                }
            }
        }
        try:
            resp = requests.post(callback_url, json=daraja_payload,
                                 headers={'Authorization': f'Bearer {API_KEY}'},
                                 timeout=10)
            _log(f"STK flow callback: {resp.status_code} {resp.text}")
        except requests.ConnectionError:
            _log(f"STK flow callback failed — Odoo unreachable")

    thread = threading.Thread(target=send_callback)
    thread.daemon = True
    thread.start()

    return jsonify({
        "status": "stk_flow_started",
        "checkout_request_id": checkout_id,
        "amount": amount,
        "phone": phone,
        "narration": narration,
        "callback_url": callback_url,
        "mpesa_receipt": mpesa_receipt,
        "note": "Daraja-style callback will be sent to Odoo in ~1 second",
    }), 200


# ============================================================
# SANDBOX MANAGEMENT
# ============================================================

@app.route('/sandbox/status', methods=['GET'])
def sandbox_status():
    return jsonify({
        "status": "running",
        "odo_base_url": ODOO_BASE_URL,
        "tills_registered": len(till_store),
        "transactions": len(transaction_store),
        "stk_pending": len(stk_pending),
        "tills": list(till_store.keys()),
        "stk_checkouts": list(stk_pending.keys()),
    })


@app.route('/sandbox/reset', methods=['POST'])
def sandbox_reset():
    till_store.clear()
    transaction_store.clear()
    stk_pending.clear()
    return jsonify({"status": "reset", "message": "All sandbox data cleared"})


def _send_to_odoo(endpoint, payload):
    url = f"{ODOO_BASE_URL}/api/dtb/{endpoint}"
    try:
        resp = requests.post(
            url, json=payload,
            headers={'Authorization': f'Bearer {API_KEY}'},
            timeout=10,
        )
        result = resp.json()
        result['_sent_payload'] = payload
        return jsonify(result), resp.status_code
    except requests.ConnectionError:
        return jsonify({
            "error": "Odoo unreachable",
            "_sent_payload": payload,
            "_note": f"Start Odoo, or set ODOO_BASE_URL (currently {ODOO_BASE_URL})",
        }), 502


def _log(msg):
    print(f"[Sandbox] {datetime.now().strftime('%H:%M:%S')} {msg}")


# ============================================================
# CLI Test Helper
# ============================================================

def run_cli_test(args=None):
    """Run from the command line to test both C2B and STK flows."""
    print("=" * 62)
    print("  DTB Till Moja — Sandbox CLI Test")
    print("=" * 62)

    till_number = str(till_counter[0] + 1)
    till_counter[0] += 1
    till_store[till_number] = {
        'till_number': till_number,
        'till_name': 'CLI Test Till',
        'status': 'ACTIVE',
    }
    print(f"\n[Setup] Till {till_number} created")

    # --- C2B Flow ---
    print(f"\n{'─' * 62}")
    print("  FLOW 1: Till Moja (C2B) — Validate + Callback")
    print(f"{'─' * 62}")

    print(f"\n  [1/6] Validating reference with Odoo...")
    try:
        resp = requests.get(
            f"{ODOO_BASE_URL}/api/dtb/validate-reference",
            params={'tillNumber': till_number, 'referenceNumber': 'INV/2026/001',
                     'transactionAmount': '1500'},
            headers={'Authorization': f'Bearer {API_KEY}'},
            timeout=10,
        )
        print(f"    Response ({resp.status_code}): {resp.json()}")
    except requests.ConnectionError:
        print(f"    Odoo unreachable — skipping")

    print(f"\n  [2/6] Sending C2B callback to Odoo...")
    xref = _generate_xref()
    c2b_callback = {
        "xref": xref,
        "cbs_reference": f"CBS{uuid.uuid4().hex[:10].upper()}",
        "cbs_module": "RT",
        "account_number": till_number,
        "branch_code": "023",
        "currency": "KES",
        "transaction_time": datetime.now().strftime("%Y%m%d %H:%M:%S"),
        "value_date": datetime.now().strftime("%Y%m%d"),
        "amount": "1500",
        "reversal_indicator": "n",
        "debit_credit_indicator": "C",
        "exchange_rate": "1",
        "financial_year": f"FY{datetime.now().year}",
        "customer_name": "CLI Test Patient",
        "customer_mobile": "254700000000",
        "narration": "INV/2026/001",
    }
    try:
        resp = requests.post(
            f"{ODOO_BASE_URL}/api/dtb/callback/notification",
            json=c2b_callback,
            headers={'Authorization': f'Bearer {API_KEY}'},
            timeout=10,
        )
        print(f"    Response ({resp.status_code}): {resp.json()}")
    except requests.ConnectionError:
        print(f"    Odoo unreachable")

    print(f"\n  [3/6] Testing C2B idempotency (same xref)...")
    try:
        resp = requests.post(
            f"{ODOO_BASE_URL}/api/dtb/callback/notification",
            json=c2b_callback,
            headers={'Authorization': f'Bearer {API_KEY}'},
            timeout=10,
        )
        r = resp.json()
        if r.get('ack_code') == '00':
            print(f"    ✓ Idempotency OK — duplicate correctly handled")
    except requests.ConnectionError:
        print(f"    Odoo unreachable")

    # --- STK Flow ---
    print(f"\n{'─' * 62}")
    print("  FLOW 2: STK Push (B2C) — Initiate + Callback")
    print(f"{'─' * 62}")

    print(f"\n  [4/6] Sending STK Push to DTB (simulated)...")
    stk_counter[0] += 1
    checkout_id = f"ws_CO_CLI_{stk_counter[0]}"
    print(f"    CheckoutRequestID: {checkout_id}")

    print(f"\n  [5/6] Sending Daraja-style STK callback to Odoo...")
    daraja_callback = {
        "Body": {
            "stkCallback": {
                "MerchantRequestID": f"MRID_{uuid.uuid4().hex[:8].upper()}",
                "CheckoutRequestID": checkout_id,
                "ResultCode": 0,
                "ResultDesc": "The service request is processed successfully.",
                "CallbackMetadata": {
                    "Item": [
                        {"Name": "Amount", "Value": 1500.0},
                        {"Name": "MpesaReceiptNumber", "Value": f"RGH{uuid.uuid4().hex[:7].upper()}"},
                        {"Name": "PhoneNumber", "Value": 254790999957},
                    ]
                }
            }
        }
    }
    # First set up the pending STK transaction in Odoo
    print(f"    (First create a pending_stk transaction in Odoo with this checkout_id)")
    try:
        resp = requests.post(
            f"{ODOO_BASE_URL}/api/dtb/stk-callback",
            json=daraja_callback,
            headers={'Authorization': f'Bearer {API_KEY}'},
            timeout=10,
        )
        print(f"    Response ({resp.status_code}): {resp.json()}")
    except requests.ConnectionError:
        print(f"    Odoo unreachable")

    # --- Summary ---
    print(f"\n{'─' * 62}")
    print(f"  [6/6] Sandbox Status")
    print(f"{'─' * 62}")
    print(f"  Tills: {list(till_store.keys())}")
    print(f"  Odoo URL: {ODOO_BASE_URL}")
    print(f"  DTB API Key: {API_KEY}")
    print(f"\n{'=' * 62}")
    print("  CLI test complete.")
    print(f"  To start mock server: python {__file__}")
    print(f"{'=' * 62}")


if __name__ == '__main__':
    import sys
    if '--cli-test' in sys.argv:
        run_cli_test()
    else:
        print(f"DTB Till Moja Sandbox running on http://{HOST}:{PORT}")
        print(f"Odoo base URL: {ODOO_BASE_URL}")
        print(f"API Key: {API_KEY}")
        print(f"\n── Till Moja (C2B) Endpoints ──")
        print(f"  All /till-moja/* endpoints for till management")
        print(f"  POST /sandbox/send-payment         — Send C2B callback")
        print(f"  POST /sandbox/trigger-payment-flow — Full C2B flow")
        print(f"\n── STK Push (B2C) Endpoints ──")
        print(f"  POST /till-moja/stk-push           — Initiate STK Push (called by Odoo)")
        print(f"  POST /sandbox/send-stk-push        — Simulate Odoo→DTB STK + callback to Odoo")
        print(f"  POST /sandbox/simulate-stk-flow    — Full STK flow with auto-callback")
        print(f"\n── Management ──")
        print(f"  POST /sandbox/reset                — Reset all data")
        print(f"  GET  /sandbox/status               — Server status")
        print(f"\n── CLI Test ──")
        print(f"  python {__file__} --cli-test")
        app.run(host=HOST, port=PORT, debug=True)
