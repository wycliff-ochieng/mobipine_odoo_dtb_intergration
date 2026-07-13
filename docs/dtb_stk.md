## Safaricom vs. DTB: Where to Focus?

From a **technical and development perspective, your primary focus is entirely on DTB Till Moja**. 

* **No direct Safaricom integration:** You do not need to register on Safaricom's Daraja portal, write code for Safaricom's APIs, or manage Safaricom's security credentials.
* **DTB acts as the proxy:** DTB wraps Safaricom’s services within the "Till Moja" API. When you want to trigger an STK Push, you call DTB, and DTB calls Safaricom on your behalf.
* **Administrative requirement:** Operationally (non-technical), your business still needs to sign up for a Till/Paybill through DTB. DTB acts as the custodian of the Till and configures the routing rules at Safaricom's end.

---

## Detailed STK Push Data Flow

Here is the exact step-by-step data and communication flow for an STK Push payment, tracing it from Odoo to Safaricom, and back again.

### Architectural Sequence Diagram

```
[Customer Browser]     [Odoo Server]       [DTB Gateway]       [Safaricom M-Pesa]     [Customer Phone]
        |                    |                   |                      |                    |
        |-- 1. Clicks Pay -->|                   |                      |                    |
        |   & enters phone   |                   |                      |                    |
        |                    |-- 2. STK Request >|                      |                    |
        |                    |   (HTTP POST)     |-- 3. Daraja API ---->|                    |
        |                    |                   |   Request            |-- 4. Push Prompt ->|
        |                    |                   |                      |    (USSD popup)    |
        |                    |                   |                      |                    |
        |                    |                   |                      |<-- 5. Enters PIN --|
        |                    |                   |<-- 6. Settlement ----|                    |
        |                    |                   |    Notification      |                    |
        |                    |                   |                      |                    |
        |                    |                   | [DTB Credits Ledger] |                    |
        |                    |<-- 7. Callback ---|                      |                    |
        |                    |   (HTTP POST)     |                      |                    |
        |                    |                   |                      |                    |
        |                    | [Reconciles State]|                      |                    |
        |<-- 8. Paid State --|                   |                      |                    |
```

---

### Step-by-Step Breakdown

#### Step 1: Customer Action in Odoo (Frontend)
* **What happens:** The customer is on your Odoo e-commerce checkout page or invoice payment portal. They select "M-Pesa Express" (STK Push), enter their phone number (e.g., `254790999957`), and click **Pay**.
* **Payload inside Odoo:** The browser sends the phone number and invoice ID to the Odoo backend.

#### Step 2: Odoo to DTB Gateway (API Call)
* **What happens:** Odoo receives the browser request and makes an outgoing HTTP secure `POST` call to the DTB Till Moja Gateway.
* **Key data sent:**
  * DTB authentication keys (Bearer/API Key).
  * The Till Number.
  * The transaction amount (e.g., `1500`).
  * The customer's phone number (`254790999957`).
  * The invoice/reference identifier (`INV/2026/0001`).

#### Step 3: DTB Gateway to Safaricom (Internal Routing)
* **What happens:** The DTB Gateway receives Odoo's request. It checks that your Till is authorized and active. DTB then translates this request into Safaricom’s official **Daraja API format** and sends it securely to Safaricom's systems.
* **Why this is helpful:** DTB handles the Safaricom authentication tokens and SSL certificates for you in this step.

#### Step 4: Safaricom to Customer’s Mobile Phone (The Prompt)
* **What happens:** Safaricom receives the request from DTB. It locates the active SIM card for the phone number `254790999957` on the GSM network and sends an encrypted **STK Prompt** (a network popup message).
* **The result:** The customer's mobile phone screen lights up automatically with the message: *"Do you want to pay KES 1,500 to DTB Merchant XYZ? Enter PIN:"*

#### Step 5: Customer Enters PIN
* **What happens:** The customer keys in their M-Pesa PIN on their phone keypad and presses **Send**.
* **The network path:** The phone securely transmits the encrypted PIN back to the Safaricom network.

#### Step 6: Safaricom Settlement to DTB
* **What happens:** Safaricom decrypts the PIN, verifies the customer has a sufficient wallet balance, deducts `KES 1,500` from the customer's wallet, and transfers those funds to DTB's pooled settlement account.
* **The notification:** Safaricom instantly sends a secure success notification to the **DTB Gateway**.

#### Step 7: DTB Core Bank Account Credit & Webhook Notification
* **What happens:** 
  1. DTB receives the success notification from Safaricom.
  2. DTB’s core banking system automatically credits your actual business bank account (`account_id` defined during creation) with the settled funds.
  3. DTB’s gateway issues a `POST /till-moja/callback/notification` callback request directly to your public Odoo endpoint (the Ngrok URL during testing or your production server).

#### Step 8: Odoo Processes Payment & Updates Client
* **What happens:** Odoo's controller receives the POST request. It validates that the message is authentic, creates a matching `account.payment` record, reconciles it to the invoice, and updates the invoice status to **Paid**.
* **The client experience:** The next time the client's browser polls or refreshes the invoice page, Odoo displays a "Payment Received - Thank You" message.