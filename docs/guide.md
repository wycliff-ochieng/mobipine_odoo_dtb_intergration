This document outlines a proposed system design for integrating Odoo ERP with
the Diamond Trust Bank (DTB) "Till Moja" API suite to facilitate automated
M-Pesa payment processing, reference validation, and automated reconciliation.

1. Architectural Overview

The integration relies on three primary components interacting asynchronously:

1.  M-Pesa Network: The customer initiates the transaction using Paybill/Till.
2.  DTB Gateway (Till Moja platform): Processes transactions, routes payments to
    the bank ledger, and manages payment routing parameters.
3.  Odoo ERP: Generates invoices/sale orders, acts as the Reference Validator,
    receives payment callbacks, and automates reconciliation.

High-Level Component Relationship

+-------------------+           +-----------------------+           +------------------+
|    M-Pesa /       |           |   DTB Gateway         |           |    Odoo ERP      |
|    Customer       |           |   (Till Moja APIs)    |           |    Instance      |
+-------------------+           +-----------------------+           +------------------+
          |                                 |                                 |
          |-- 1. Initiates Paybill/Till --->|                                 |
          |   (with Invoice/Ref Number)     |-- 2. Query Reference Validation |
          |                                 |      (Dynamic/External URL) --->|
          |                                 |                                 |
          |                                 |<-- 3. Validation Response ------|
          |                                 |      (Allow/Deny Payment)       |
          |<-- 4. Payment Success/Failure --|                                 |
          |                                 |-- 5. Post Transaction Callback |
          |                                 |      (Callback URL) ----------->|
          |                                 |                                 |
          |                                 |<-- 6. Acknowledge Receipt ------|

2. Key Integration Workflows

The system design accommodates two primary real-time patterns: Reference
Validation (pre-payment check) and Payment Notification (post-payment
settlement).

Workflow A: External Reference Validation (Pre-Payment Check)

To prevent customers from keying in incorrect references or wrong amounts, DTB
queries Odoo in real-time before accepting the customer's cash.

M-Pesa User            DTB Gateway (Till Moja)                 Odoo ERP (Controller)
    |                             |                                      |
    |--- Enter Ref & Amount ----->|                                      |
    |                             |--- GET /query-external-reference --->|
    |                             |    (Till, Ref, Amount)               |
    |                             |                                      | [Validate: Is Invoice active?]
    |                             |                                      | [Validate: Does amount match?]
    |                             |<-- JSON Response (Allow/Block) ------|
    |<-- Confirm/Reject Payment --|                                      |

Workflow B: Post-Payment Settlement Callback

Once DTB processes the payment, it sends an asynchronous notification to Odoo.
Odoo registers this payment in the general ledger and marks the invoice as paid.

DTB Gateway (Till Moja)                              Odoo ERP (Webhook Controller)
    |                                                              |
    |--- POST /till-moja/callback/notification (JSON payload) ---->|
    |                                                              | [Check Idempotency (xref)]
    |                                                              | [Create account.payment record]
    |                                                              | [Reconcile with Invoice / Sale Order]
    |<-- POST Response 200 (ACK "SUCCESS") ------------------------|

3. Odoo Custom Module Design

To implement this design, a custom Odoo module (e.g., l10n_ke_dtb_moja) is
required.

l10n_ke_dtb_moja/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   └── main.py             # External Validation & Callback Webhook Endpoints
├── models/
│   ├── __init__.py
│   ├── dtb_till.py         # Config/Credentials for DTB Tills
│   ├── dtb_transaction.py  # Log of incoming transactions & trace records
│   └── account_payment.py  # Custom logic to process payments
└── views/
    ├── dtb_till_views.xml
    ├── dtb_transaction_views.xml
    └── account_payment_views.xml

Database Schema Additions

1. DTB Till Config (dtb.moja.till)

Stores configurations for authorized tills used in Odoo payment journals.

  - name (Char): Friendly name
  - till_number (Char, unique): The merchant Till Number
  - user_id (Char): API authentication credential
  - password (Char): Securely stored API password
  - channel (Char): "MBS" or designated system channel
  - journal_id (Many2one): Points to account.journal associated with this Till
    (Bank/Cash)

2. DTB Transaction Logs (dtb.moja.transaction)

Tracks incoming webhooks to ensure audits can be performed and to protect
against duplicate actions.

  - xref (Char, unique index): DTB transaction reference used for idempotency
  - cbs_reference (Char): Core banking system reference
  - amount (Monetary): Received amount
  - customer_name (Char): Name of paying party
  - customer_mobile (Char): Payer phone number
  - state (Selection): draft -> processed -> failed -> reversed
  - error_reason (Text): Capture detail if reconciliation fails

4. Endpoint Specifications for Odoo Controllers

Endpoint 1: Reference Validation (GET)

This route must match the pattern defined in your DTB configuration (or as
updated in the validation_url).

  - Route: /api/dtb/validate-reference
  - Query Parameters:
      - tillNumber (string)
      - referenceNumber (string)
      - transactionAmount (float)

Python Implementation Logic

from odoo import http
from odoo.http import request
import json

class DtbValidationController(http.Controller):

    @http.route('/api/dtb/validate-reference', type='http', auth='none', methods=['GET'], csrf=False)
    def validate_reference(self, **kwargs):
        till_number = kwargs.get('tillNumber')
        reference = kwargs.get('referenceNumber')
        amount = float(kwargs.get('transactionAmount', 0))

        # Perform authentication check (e.g., check API key in Headers)
        api_key = request.httprequest.headers.get('Authorization')
        if not self._is_authorized(api_key):
             return request.make_response(json.dumps({"error": "Unauthorized"}), headers=[('Content-Type', 'application/json')], status=401)

        # Search for matching invoice/sale order in Odoo
        # E.g., reference matches account.move name or customized payment reference field
        invoice = request.env['account.move'].sudo().search([
            ('payment_reference', '=', reference),
            ('state', '=', 'posted'),
            ('payment_state', 'not in', ('paid', 'in_payment'))
        ], limit=1)

        if not invoice:
            return request.make_response(json.dumps({"error": "Reference not found"}), status=404)

        # Check if the payment matches expected amount constraints
        # Some designs allow partial payments, others require exact matching
        if amount <= 0:
            return request.make_response(json.dumps({"error": "Invalid Amount"}), status=400)

        response_payload = {
            "till_number": till_number,
            "reference_id": reference,
            "value_1": invoice.partner_id.name,
            "value_2": invoice.name,
            "value_3": str(invoice.amount_residual),
            "value_4": "",
            "value_5": ""
        }
        return request.make_response(json.dumps(response_payload), headers=[('Content-Type', 'application/json')], status=200)

Endpoint 2: Payment Callback Webhook (POST)

Receives notification payloads from the DTB system upon settlement.

  - Route: /api/dtb/callback/notification
  - Method: POST

Python Implementation Logic

    @http.route('/api/dtb/callback/notification', type='json', auth='none', methods=['POST'], csrf=False)
    def payment_callback(self):
        payload = request.jsonrequest
        xref = payload.get('xref')
        cbs_ref = payload.get('cbs_reference')
        amount = float(payload.get('amount'))
        reference = payload.get('narration')  # Assuming narration contains the target payment reference

        # 1. Idempotency Check
        existing_tx = request.env['dtb.moja.transaction'].sudo().search([('xref', '=', xref)], limit=1)
        if existing_tx:
            return {
                "xref": xref,
                "user_reference": existing_tx.name,
                "ack_code": "00",
                "ack_description": "SUCCESS" # Already processed
            }

        # 2. Lock Row to prevent race conditions during concurrent webhook retries
        # Using PostgreSQL SELECT FOR UPDATE
        request.env.cr.execute("SELECT id FROM dtb_moja_transaction WHERE xref = %s FOR UPDATE NOWAIT", (xref,))

        # 3. Process Payment Registration
        try:
            # Create local log
            tx_log = request.env['dtb.moja.transaction'].sudo().create({
                'xref': xref,
                'cbs_reference': cbs_ref,
                'amount': amount,
                'customer_name': payload.get('customer_name'),
                'customer_mobile': payload.get('customer_mobile'),
                'state': 'draft'
            })

            # Search corresponding Invoice
            invoice = request.env['account.move'].sudo().search([
                ('payment_reference', '=', reference),
                ('state', '=', 'posted')
            ], limit=1)

            if invoice:
                # Register payment against the invoice
                payment_method = request.env.ref('l10n_ke_dtb_moja.account_payment_method_dtb_moja')
                payment = request.env['account.payment'].sudo().create({
                    'payment_type': 'inbound',
                    'partner_type': 'customer',
                    'partner_id': invoice.partner_id.id,
                    'amount': amount,
                    'journal_id': tx_log.get_associated_journal(), # Determined based on Till
                    'payment_method_id': payment_method.id,
                    'ref': f"DTB M-Pesa: {cbs_ref}",
                })
                payment.action_post()
                
                # Reconcile invoice
                (payment.line_ids + invoice.line_ids).filtered(
                    lambda line: line.account_id == invoice.outstanding_line_ids.account_id
                ).reconcile()

                tx_log.write({'state': 'processed'})
                
                return {
                    "xref": xref,
                    "user_reference": payment.name,
                    "ack_code": "00",
                    "ack_description": "SUCCESS"
                }
            else:
                # Log transaction as unassociated/unreconciled for manual intervention
                tx_log.write({'state': 'failed', 'error_reason': 'Invoice reference matching failed'})
                return {
                    "xref": xref,
                    "user_reference": "MANUAL_RECONCILIATION_REQUIRED",
                    "ack_code": "00", # Respond with Success to prevent endless gateway retries
                    "ack_description": "UNMATCHED_REFERENCE"
                }

        except Exception as e:
            request.env.cr.rollback()
            return {
                "xref": xref,
                "user_reference": "",
                "ack_code": "99",
                "ack_description": f"SYSTEM_ERROR: {str(e)}"
            }

5. Security & Network Considerations

1.  IP Whitelisting & Firewall: Restrict incoming connections to the
    /api/dtb/... controllers. Allow traffic only from known DTB Gateway IP
    addresses.
2.  Transport Layer Security (TLS): Force production Odoo installations to
    execute webhooks over HTTPS (TLS 1.2 or TLS 1.3).
3.  Authentication Token validation: Enforce authorization headers
    (bearerAuthApiKeyAuth) in both the validation URL and Callback endpoints.
4.  Data Sanitization: Sanitize path parameters and payload inputs before
    evaluating database transactions to mitigate security risks.

6. Fault Tolerance and Edge Cases

Callback Re-delivery & Retry Mechanism

  - Scenario: Odoo experiences transient downtime when DTB attempts to deliver a
    payment notification.
  - Design Action: The system expects DTB to retry delivery. Odoo's webhook uses
    PostgreSQL constraints on xref unique indices to drop retry requests once
    the payment is already committed, preventing duplicate credit/posting.

Partial or Overpayments

  - Scenario: The client changes the payment amount inside their M-Pesa client
    during payment.
  - Design Action:
      - If External Validation is strict, the Odoo /validate-reference
        controller should return an HTTP 400 status if transactionAmount does
        not equal the target outstanding invoice balance
        (invoice.amount_residual). This causes M-Pesa to reject the transaction
        before funds leave the user's wallet.
      - If the system allows partial payments, the validation service accepts
        any amount up to invoice.amount_residual. Any overpayment defaults to an
        unreconciled credit on the customer's account statement.
