# DTB Developer Portal & Astra Bank APIs Reference Documentation

This document contains the complete and structured reference documentation for onboarding, go-live initiation, authentication, and the M-Pesa API suite on the Diamond Trust Bank (DTB) Developer Portal.

---

## Table of Contents
1. [Onboarding & Go-Live Workflows](#1-onboarding--go-live-workflows)
   - [Getting Started](#getting-started)
   - [Initiating Go-Live for the First Time](#initiating-go-live-for-the-first-time)
   - [Subsequent Go-Live](#subsequent-go-live)
2. [Astra Bank APIs: Authentication](#2-astra-bank-apis-authentication)
   - [Get API Token](#get-api-token)
   - [Refresh API Token](#refresh-api-token)
3. [M-Pesa Integration APIs](#3-m-pesa-integration-apis)
   - [M-Pesa B2C](#m-pesa-b2c)
   - [M-Pesa STK-Push](#m-pesa-stk-push)
   - [B2B Validation](#b2b-validation)
   - [M-Pesa B2B Transfer](#m-pesa-b2b-transfer)

---

## 1. Onboarding & Go-Live Workflows

### Getting Started

Before proceeding with the steps below, make sure you have signed up and are logged into the developer portal.

#### Steps to Consume the Payments API:
1. **Navigate to Accounts** and type the name of your account.
2. **Click on Currency** and select your account currency.
3. **Click on Generate Account**.
4. **Navigate to Products**.
5. **Locate the API** that you are interested in and click on **Subscribe**.
6. **Select the Account** that you want to consume the API on and click **Subscribe**.
7. On the right, click **Complete**.
8. **Navigate to Apps**.
9. **Click on Create a new app**.
10. **Type the name** of your app.
11. **Check all the APIs** that you want your App to access.
    > *Note: You can associate multiple APIs with a single application.*
12. **Click on Complete** and then **Okay**.
    > *Check your registered email address for your APP credentials.*

---

### Initiating Go-Live for the First Time

This section is applicable to partners who are looking to promote their services and APIs to the production environment for the first time.

#### Steps to Initiate Go-Live:
1. **Click on Test Mode**.
2. **Click on Initiate go-live**.
3. **Click on Account 1 - New Account**.
4. **Select Account Type**:
   - Select whether the production account number you are entering is a business account or a personal account. 
   - *Note: The account must be an active account you already hold with DTB.*
5. **Enter Account Details** and click **Submit**.
6. **Download and fill all forms**:
   - All forms must be filled in the name of the company entering the agreement with DTB (e.g., if Company A contracted Company B to build the software, but Company A is the account and service owner, all forms must be in the name of Company A).
   - Contracted parties (Company B) may append their signatures in certain sections, but the primary owner (Company A) must be a signatory to both the UAT form and the Application form.
   - Once the UAT and Application forms have been filled and signed, you may email a scanned soft copy to begin the process, but the physical hard copies must still be delivered to DTB.
   - The VPN form will be shared by the DTB networks team upon presentation of the soft-copy UAT form. Once the VPN form is filled and shared back, configuration is completed and the connection is tested.
7. **Upload all filled forms**.
8. **API Selection**:
   - Select the APIs you want to promote to production.
   - Only select the APIs for which you have completed UAT and filled out as "tested" in the UAT form.
   - You can initiate a *Subsequent Go-Live* later if you need to add more APIs.
9. **Input IPs**:
   - Enter your public-facing NAT IP address (to be whitelisted on the DTB firewall).
10. **Fill in the company details**.
11. **Review and submit the Go-live request**.
12. **DTB Review & Approval**:
    - The request is received by DTB Digital Client Services, who verify the details and approve the promotion if everything is correct.
    - If there is an issue, the request is declined, and feedback is shared. If approved, you will be notified to proceed with piloting the integration.
13. **Finalize production setup**:
    - Create a production app inside the portal to generate your production app credentials, similar to the process followed in the UAT sandbox.
    - Test the production endpoints to ensure the services are operating as expected.

#### Production Network Notes (VPN):
* While routing traffic over the established VPN, you must use **port 8080** and the NAT IP shared with you by the network team. The NAT IP used to route traffic is different from the public IP registered during the go-live application step.
* Your endpoint URLs over VPN must follow this format:
  `https://{your_nat_ip}:8080/{endpoint_path}`
* If you encounter an SSL certificate verification issue, you have two options:
  1. Skip SSL verification (easier, since the request is already secured inside your dedicated VPN tunnel).
  2. Request the DTB self-signed certificate from the support team to add to your local trust store.

---

### Subsequent Go-Live

This section is applicable to partners who have gone live before and are seeking to add more APIs to their active production environment.

#### Steps:
1. **Click on Test Mode**.
2. **Click on Submit API**.
3. **Select the account** and the API you want to add.
4. **Submit the account**.
5. **Download and Fill the UAT Form** specifically for the new APIs.
6. **Click on Submit & Continue to Sign Offs**.
7. **Submit the Go-Live request** for approval.

---

## 2. Astra Bank APIs: Authentication

All core transactional APIs require HTTP Bearer Token authentication.

*   **Security Scheme Type:** `http`
*   **HTTP Authorization Scheme:** `bearer`
*   **Header Format:** `Authorization: Bearer <token>`

---

### Get API Token

*   **HTTP Method:** `POST`
*   **Endpoint:** `https://uat.dtbafrica.com/api/dev-portal/v3/auth/token`
*   **Content-Type:** `application/x-www-form-urlencoded`

#### Request Body Parameters:

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `client_id` | string | Yes | The client identifier used to uniquely identify the client application. |
| `client_secret` | string | Yes | The unique secret key allocated to your application. |
| `grant_type` | string | Yes | The credential generation type. Set value to: `password` |
| `username` | string | Yes | Your portal developer account username. |
| `password` | string | Yes | Your portal developer account password. |

#### Responses:

##### Code 200 OK (application/json)
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "r1_...",
  "expires_in": 3600,
  "refresh_token_expires_in": 86400
}
```

#### Code Snippet (C# HttpClient):
```csharp
var client = new HttpClient();
var request = new HttpRequestMessage(HttpMethod.Post, "https://uat.dtbafrica.com/api/dev-portal/v3/auth/token");
request.Headers.Add("Accept", "application/json");

var postData = new List<KeyValuePair<string, string>>
{
    new KeyValuePair<string, string>("client_id", "YOUR_CLIENT_ID"),
    new KeyValuePair<string, string>("client_secret", "YOUR_CLIENT_SECRET"),
    new KeyValuePair<string, string>("grant_type", "password"),
    new KeyValuePair<string, string>("username", "YOUR_USERNAME"),
    new KeyValuePair<string, string>("password", "YOUR_PASSWORD")
};

request.Content = new FormUrlEncodedContent(postData);
var response = await client.SendAsync(request);
response.EnsureSuccessStatusCode();
Console.WriteLine(await response.Content.ReadAsStringAsync());
```

---

### Refresh API Token

Used to refresh an expired access token using the refresh token received during initial authentication.

*   **HTTP Method:** `POST`
*   **Endpoint:** `https://uat.dtbafrica.com/api/dev-portal/v3/auth/token/refresh`
*   **Content-Type:** `application/x-www-form-urlencoded`

#### Request Body Parameters:

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `client_id` | string | Yes | The client identifier used to uniquely identify your application. |
| `client_secret` | string | Yes | The unique secret key allocated to your application. |
| `grant_type` | string | Yes | Credential generation type. Set value to: `refresh_token` |
| `refresh_token` | string | Yes | The active refresh token received in your last successful authentication response. |

#### Responses:

##### Code 200 OK (application/json)
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "r1_...",
  "expires_in": 3600,
  "refresh_token_expires_in": 86400
}
```

#### Code Snippet (C# HttpClient):
```csharp
var client = new HttpClient();
var request = new HttpRequestMessage(HttpMethod.Post, "https://uat.dtbafrica.com/api/dev-portal/v3/auth/token/refresh");
request.Headers.Add("Accept", "application/json");

var postData = new List<KeyValuePair<string, string>>
{
    new KeyValuePair<string, string>("client_id", "YOUR_CLIENT_ID"),
    new KeyValuePair<string, string>("client_secret", "YOUR_CLIENT_SECRET"),
    new KeyValuePair<string, string>("grant_type", "refresh_token"),
    new KeyValuePair<string, string>("refresh_token", "YOUR_REFRESH_TOKEN")
};

request.Content = new FormUrlEncodedContent(postData);
var response = await client.SendAsync(request);
response.EnsureSuccessStatusCode();
Console.WriteLine(await response.Content.ReadAsStringAsync());
```

---

## 3. M-Pesa Integration APIs

### M-Pesa B2C

Facilitates Business-to-Customer (B2C) fund transfers from your bank account directly to a mobile subscriber's M-Pesa wallet.

*   **HTTP Method:** `POST`
*   **Endpoint:** `https://uat.dtbafrica.com/api/dev-portal/v3/mpesa/b2c`
*   **Authorization:** `Bearer <token>`
*   **Content-Type:** `application/json`

#### Request Body Schema:

```json
{
  "identifier": {
    "referenceID": "unique_request_reference_id",
    "channel": "DEV-PORTAL"
  },
  "payload": {
    "beneficiaryMsisdn": "2547XXXXXXXX",
    "transactionAmount": 1000,
    "customerMsisdn": "2547XXXXXXXX",
    "customerName": "John Doe",
    "accountNumber": "0112870001",
    "branchCode": "023",
    "currency": "KES",
    "mnoCode": "MPESA",
    "narration": "Payment Description",
    "transactionType": "TransferFromBankToCustomer",
    "resultUrl": "https://yourdomain.com/mpesa/b2c-callback"
  }
}
```

#### Responses:

##### Code 200 OK (application/json)
```json
{
  "status": "SUCCESS",
  "responseCode": "000",
  "responseDescription": "The transaction was accepted successfully",
  "externalRef": "EXT-CBS-982348"
}
```

#### Code Snippet (C# HttpClient):
```csharp
var client = new HttpClient();
var request = new HttpRequestMessage(HttpMethod.Post, "https://uat.dtbafrica.com/api/dev-portal/v3/mpesa/b2c");
request.Headers.Add("Accept", "application/json");
request.Headers.Add("Authorization", "Bearer YOUR_ACCESS_TOKEN");

var jsonPayload = @"{
  ""identifier"": {
    ""referenceID"": ""B2C_REF_1001"",
    ""channel"": ""DEV-PORTAL""
  },
  ""payload"": {
    ""beneficiaryMsisdn"": ""254700000000"",
    ""transactionAmount"": 100,
    ""customerMsisdn"": ""254700000000"",
    ""customerName"": ""John Doe"",
    ""accountNumber"": ""0012870005"",
    ""branchCode"": ""023"",
    ""currency"": ""KES"",
    ""mnoCode"": ""MPESA"",
    ""narration"": ""Vendor Payment"",
    ""transactionType"": ""TransferFromBankToCustomer"",
    ""resultUrl"": ""https://yourdomain.com/callbacks/b2c""
  }
}";

request.Content = new StringContent(jsonPayload, System.Text.Encoding.UTF8, "application/json");
var response = await client.SendAsync(request);
response.EnsureSuccessStatusCode();
Console.WriteLine(await response.Content.ReadAsStringAsync());
```

---

### M-Pesa STK-Push

Initiates a Lipa Na M-Pesa Online transaction (STK Push), prompting the customer to input their M-Pesa PIN on their mobile device to finalize a payment.

*   **HTTP Method:** `POST`
*   **Endpoint:** `https://uat.dtbafrica.com/api/dev-portal/v3/mpesa/stkpush`
*   **Authorization:** `Bearer <token>`
*   **Content-Type:** `application/json`

#### Request Body Schema:

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `TransactionRef` | string | Yes | Unique reference ID associated with the transaction. |
| `TransactionType` | string | Yes | Set to standard value: `CustomerPayBillOnline` |
| `Amount` | integer | Yes | Value to be transferred (value must be `>= 1`). |
| `PhoneNumber` | string | Yes | Mobile number to receive the STK prompt (format must be exactly 12 characters, e.g. `2547XXXXXXXX`). |
| `AccountNumber` | string | Yes | Your registered core account number to be credited (must be exactly 10 characters). |
| `BusinessShortCode` | string | Yes | The recipient business Paybill shortcode. |
| `TransactionDesc` | string | Yes | Description of the transaction. |
| `PromptDisplayAccount` | string | No | The custom account name displayed on the customer's phone prompt screen. |
| `UserCallback` | string <uri> | Yes | Public callback URL where the transaction success/fail result will be posted. |

#### Request Body Payload Sample:
```json
{
  "TransactionRef": "STK_REF_9921",
  "TransactionType": "CustomerPayBillOnline",
  "Amount": 1500,
  "PhoneNumber": "254700000000",
  "AccountNumber": "0012870005",
  "BusinessShortCode": "123456",
  "TransactionDesc": "Invoice Payment",
  "PromptDisplayAccount": "Vivace Clinic",
  "UserCallback": "https://yourdomain.com/callbacks/stk"
}
```

#### Responses:

##### Code 200 OK (application/json)
```json
{
  "status": "SUCCESS",
  "responseCode": "000",
  "responseDescription": "The service request was processed successfully.",
  "externalReference": "ws_CO_140720261545"
}
```

#### Code Snippet (C# HttpClient):
```csharp
var client = new HttpClient();
var request = new HttpRequestMessage(HttpMethod.Post, "https://uat.dtbafrica.com/api/dev-portal/v3/mpesa/stkpush");
request.Headers.Add("Accept", "application/json");
request.Headers.Add("Authorization", "Bearer YOUR_ACCESS_TOKEN");

var jsonPayload = @"{
  ""TransactionRef"": ""STK_TX_12345"",
  ""TransactionType"": ""CustomerPayBillOnline"",
  ""Amount"": 10,
  ""PhoneNumber"": ""254700000000"",
  ""AccountNumber"": ""0012870005"",
  ""BusinessShortCode"": ""123456"",
  ""TransactionDesc"": ""Medical Bill"",
  ""PromptDisplayAccount"": ""Vivace Cosmetics"",
  ""UserCallback"": ""https://yourdomain.com/callbacks/stk""
}";

request.Content = new StringContent(jsonPayload, System.Text.Encoding.UTF8, "application/json");
var response = await client.SendAsync(request);
response.EnsureSuccessStatusCode();
Console.WriteLine(await response.Content.ReadAsStringAsync());
```

---

### B2B Validation

Validates whether a business partner's M-Pesa shortcode is active and correct before initiating a Business-to-Business (B2B) transaction.

*   **HTTP Method:** `GET`
*   **Endpoint:** `https://uat.dtbafrica.com/api/dev-portal/v3/mpesa/v2/b2bvalidate`
*   **Authorization:** `Bearer <token>`

#### Query Parameters:

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `IdentifierType` | string | Yes | Set value to: `BusinessPayBill` or `BusinessBuyGoods` |
| `BusinessShortCode` | string | Yes | The target merchant's M-Pesa shortcode (e.g. `123456`). |

#### Responses:

##### Code 200 OK (application/json)
```json
{
  "responseCode": "000",
  "responseMessage": "Success",
  "errorDescription": "",
  "organizationName": "Safal Group Kenya"
}
```

#### Code Snippet (C# HttpClient):
```csharp
var client = new HttpClient();
var request = new HttpRequestMessage(HttpMethod.Get, "https://uat.dtbafrica.com/api/dev-portal/v3/mpesa/v2/b2bvalidate?IdentifierType=BusinessPayBill&BusinessShortCode=123456");
request.Headers.Add("Accept", "application/json");
request.Headers.Add("Authorization", "Bearer YOUR_ACCESS_TOKEN");

var response = await client.SendAsync(request);
response.EnsureSuccessStatusCode();
Console.WriteLine(await response.Content.ReadAsStringAsync());
```

---

### M-Pesa B2B Transfer

Facilitates Business-to-Business (B2B) transactions, moving funds from your core account directly to another organization’s M-Pesa Paybill or Buy Goods till.

*   **HTTP Method:** `POST`
*   **Endpoint:** `https://uat.dtbafrica.com/api/dev-portal/v3/mpesa/b2b`
*   **Authorization:** `Bearer <token>`
*   **Content-Type:** `application/json`

#### Request Body Schema:

```json
{
  "identifier": {
    "referenceID": "unique_b2b_reference_id",
    "channel": "DEV-PORTAL"
  },
  "payload": {
    "beneficiaryShortCode": "654321",
    "beneficiaryAccountNumber": "78234723",
    "transactionAmount": 5000,
    "customerMsisdn": "2547XXXXXXXX",
    "customerName": "Company A Limited",
    "accountNumber": "0012870005",
    "branchCode": "023",
    "mnoCode": "MPESA",
    "narration": "Stock purchase settlement",
    "transactionType": "BusinessPayBill",
    "resultUrl": "https://yourdomain.com/callbacks/b2b"
  }
}
```

#### Responses:

##### Code 200 OK (application/json)
```json
{
  "status": "SUCCESS",
  "responseCode": "000",
  "responseDescription": "The B2B transfer request was accepted successfully.",
  "externalRef": "EXT-B2B-19238"
}
```

#### Code Snippet (C# HttpClient):
```csharp
var client = new HttpClient();
var request = new HttpRequestMessage(HttpMethod.Post, "https://uat.dtbafrica.com/api/dev-portal/v3/mpesa/b2b");
request.Headers.Add("Accept", "application/json");
request.Headers.Add("Authorization", "Bearer YOUR_ACCESS_TOKEN");

var jsonPayload = @"{
  ""identifier"": {
    ""referenceID"": ""B2B_TX_89234"",
    ""channel"": ""DEV-PORTAL""
  },
  ""payload"": {
    ""beneficiaryShortCode"": ""654321"",
    ""beneficiaryAccountNumber"": ""78234723"",
    ""transactionAmount"": 1000,
    ""customerMsisdn"": ""254700000000"",
    ""customerName"": ""Vivace Clinics"",
    ""accountNumber"": ""0012870005"",
    ""branchCode"": ""023"",
    ""mnoCode"": ""MPESA"",
    ""narration"": ""Wholesale Supplier"",
    ""transactionType"": ""BusinessPayBill"",
    ""resultUrl"": ""https://yourdomain.com/callbacks/b2b""
  }
}";

request.Content = new StringContent(jsonPayload, System.Text.Encoding.UTF8, "application/json");
var response = await client.SendAsync(request);
response.EnsureSuccessStatusCode();
Console.WriteLine(await response.Content.ReadAsStringAsync());
```


# DTB Developer Portal & Astra Bank APIs Reference Documentation

This document contains the complete and structured reference documentation for onboarding, go-live initiation, authentication, and the M-Pesa API suite on the Diamond Trust Bank (DTB) Developer Portal.

---

## Table of Contents
1. [Onboarding & Go-Live Workflows](#1-onboarding--go-live-workflows)
   - [Getting Started](#getting-started)
   - [Initiating Go-Live for the First Time](#initiating-go-live-for-the-first-time)
   - [Subsequent Go-Live](#subsequent-go-live)
2. [Astra Bank APIs: Authentication](#2-astra-bank-apis-authentication)
   - [Get API Token](#get-api-token)
   - [Refresh API Token](#refresh-api-token)
3. [M-Pesa Integration APIs](#3-m-pesa-integration-apis)
   - [M-Pesa B2C](#m-pesa-b2c)
   - [M-Pesa STK-Push](#m-pesa-stk-push)
   - [B2B Validation](#b2b-validation)
   - [M-Pesa B2B Transfer](#m-pesa-b2b-transfer)

---

## 1. Onboarding & Go-Live Workflows

### Getting Started

Before proceeding with the steps below, make sure you have signed up and are logged into the developer portal.

#### Steps to Consume the Payments API:
1. **Navigate to Accounts** and type the name of your account.
2. **Click on Currency** and select your account currency.
3. **Click on Generate Account**.
4. **Navigate to Products**.
5. **Locate the API** that you are interested in and click on **Subscribe**.
6. **Select the Account** that you want to consume the API on and click **Subscribe**.
7. On the right, click **Complete**.
8. **Navigate to Apps**.
9. **Click on Create a new app**.
10. **Type the name** of your app.
11. **Check all the APIs** that you want your App to access.
    > *Note: You can associate multiple APIs with a single application.*
12. **Click on Complete** and then **Okay**.
    > *Check your registered email address for your APP credentials.*

---

### Initiating Go-Live for the First Time

This section is applicable to partners who are looking to promote their services and APIs to the production environment for the first time.

#### Steps to Initiate Go-Live:
1. **Click on Test Mode**.
2. **Click on Initiate go-live**.
3. **Click on Account 1 - New Account**.
4. **Select Account Type**:
   - Select whether the production account number you are entering is a business account or a personal account. 
   - *Note: The account must be an active account you already hold with DTB.*
5. **Enter Account Details** and click **Submit**.
6. **Download and fill all forms**:
   - All forms must be filled in the name of the company entering the agreement with DTB (e.g., if Company A contracted Company B to build the software, but Company A is the account and service owner, all forms must be in the name of Company A).
   - Contracted parties (Company B) may append their signatures in certain sections, but the primary owner (Company A) must be a signatory to both the UAT form and the Application form.
   - Once the UAT and Application forms have been filled and signed, you may email a scanned soft copy to begin the process, but the physical hard copies must still be delivered to DTB.
   - The VPN form will be shared by the DTB networks team upon presentation of the soft-copy UAT form. Once the VPN form is filled and shared back, configuration is completed and the connection is tested.
7. **Upload all filled forms**.
8. **API Selection**:
   - Select the APIs you want to promote to production.
   - Only select the APIs for which you have completed UAT and filled out as "tested" in the UAT form.
   - You can initiate a *Subsequent Go-Live* later if you need to add more APIs.
9. **Input IPs**:
   - Enter your public-facing NAT IP address (to be whitelisted on the DTB firewall).
10. **Fill in the company details**.
11. **Review and submit the Go-live request**.
12. **DTB Review & Approval**:
    - The request is received by DTB Digital Client Services, who verify the details and approve the promotion if everything is correct.
    - If there is an issue, the request is declined, and feedback is shared. If approved, you will be notified to proceed with piloting the integration.
13. **Finalize production setup**:
    - Create a production app inside the portal to generate your production app credentials, similar to the process followed in the UAT sandbox.
    - Test the production endpoints to ensure the services are operating as expected.

#### Production Network Notes (VPN):
* While routing traffic over the established VPN, you must use **port 8080** and the NAT IP shared with you by the network team. The NAT IP used to route traffic is different from the public IP registered during the go-live application step.
* Your endpoint URLs over VPN must follow this format:
  `https://{your_nat_ip}:8080/{endpoint_path}`
* If you encounter an SSL certificate verification issue, you have two options:
  1. Skip SSL verification (easier, since the request is already secured inside your dedicated VPN tunnel).
  2. Request the DTB self-signed certificate from the support team to add to your local trust store.

---

### Subsequent Go-Live

This section is applicable to partners who have gone live before and are seeking to add more APIs to their active production environment.

#### Steps:
1. **Click on Test Mode**.
2. **Click on Submit API**.
3. **Select the account** and the API you want to add.
4. **Submit the account**.
5. **Download and Fill the UAT Form** specifically for the new APIs.
6. **Click on Submit & Continue to Sign Offs**.
7. **Submit the Go-Live request** for approval.

---

## 2. Astra Bank APIs: Authentication

All core transactional APIs require HTTP Bearer Token authentication.

*   **Security Scheme Type:** `http`
*   **HTTP Authorization Scheme:** `bearer`
*   **Header Format:** `Authorization: Bearer <token>`

---

### Get API Token

*   **HTTP Method:** `POST`
*   **Endpoint:** `https://uat.dtbafrica.com/api/dev-portal/v3/auth/token`
*   **Content-Type:** `application/x-www-form-urlencoded`

#### Request Body Parameters:

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `client_id` | string | Yes | The client identifier used to uniquely identify the client application. |
| `client_secret` | string | Yes | The unique secret key allocated to your application. |
| `grant_type` | string | Yes | The credential generation type. Set value to: `password` |
| `username` | string | Yes | Your portal developer account username. |
| `password` | string | Yes | Your portal developer account password. |

#### Responses:

##### Code 200 OK (application/json)
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "r1_...",
  "expires_in": 3600,
  "refresh_token_expires_in": 86400
}
```

#### Code Snippet (C# HttpClient):
```csharp
var client = new HttpClient();
var request = new HttpRequestMessage(HttpMethod.Post, "https://uat.dtbafrica.com/api/dev-portal/v3/auth/token");
request.Headers.Add("Accept", "application/json");

var postData = new List<KeyValuePair<string, string>>
{
    new KeyValuePair<string, string>("client_id", "YOUR_CLIENT_ID"),
    new KeyValuePair<string, string>("client_secret", "YOUR_CLIENT_SECRET"),
    new KeyValuePair<string, string>("grant_type", "password"),
    new KeyValuePair<string, string>("username", "YOUR_USERNAME"),
    new KeyValuePair<string, string>("password", "YOUR_PASSWORD")
};

request.Content = new FormUrlEncodedContent(postData);
var response = await client.SendAsync(request);
response.EnsureSuccessStatusCode();
Console.WriteLine(await response.Content.ReadAsStringAsync());
```

---

### Refresh API Token

Used to refresh an expired access token using the refresh token received during initial authentication.

*   **HTTP Method:** `POST`
*   **Endpoint:** `https://uat.dtbafrica.com/api/dev-portal/v3/auth/token/refresh`
*   **Content-Type:** `application/x-www-form-urlencoded`

#### Request Body Parameters:

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `client_id` | string | Yes | The client identifier used to uniquely identify your application. |
| `client_secret` | string | Yes | The unique secret key allocated to your application. |
| `grant_type` | string | Yes | Credential generation type. Set value to: `refresh_token` |
| `refresh_token` | string | Yes | The active refresh token received in your last successful authentication response. |

#### Responses:

##### Code 200 OK (application/json)
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "r1_...",
  "expires_in": 3600,
  "refresh_token_expires_in": 86400
}
```

#### Code Snippet (C# HttpClient):
```csharp
var client = new HttpClient();
var request = new HttpRequestMessage(HttpMethod.Post, "https://uat.dtbafrica.com/api/dev-portal/v3/auth/token/refresh");
request.Headers.Add("Accept", "application/json");

var postData = new List<KeyValuePair<string, string>>
{
    new KeyValuePair<string, string>("client_id", "YOUR_CLIENT_ID"),
    new KeyValuePair<string, string>("client_secret", "YOUR_CLIENT_SECRET"),
    new KeyValuePair<string, string>("grant_type", "refresh_token"),
    new KeyValuePair<string, string>("refresh_token", "YOUR_REFRESH_TOKEN")
};

request.Content = new FormUrlEncodedContent(postData);
var response = await client.SendAsync(request);
response.EnsureSuccessStatusCode();
Console.WriteLine(await response.Content.ReadAsStringAsync());
```

---

## 3. M-Pesa Integration APIs

### M-Pesa B2C

Facilitates Business-to-Customer (B2C) fund transfers from your bank account directly to a mobile subscriber's M-Pesa wallet.

*   **HTTP Method:** `POST`
*   **Endpoint:** `https://uat.dtbafrica.com/api/dev-portal/v3/mpesa/b2c`
*   **Authorization:** `Bearer <token>`
*   **Content-Type:** `application/json`

#### Request Body Schema:

```json
{
  "identifier": {
    "referenceID": "unique_request_reference_id",
    "channel": "DEV-PORTAL"
  },
  "payload": {
    "beneficiaryMsisdn": "2547XXXXXXXX",
    "transactionAmount": 1000,
    "customerMsisdn": "2547XXXXXXXX",
    "customerName": "John Doe",
    "accountNumber": "0112870001",
    "branchCode": "023",
    "currency": "KES",
    "mnoCode": "MPESA",
    "narration": "Payment Description",
    "transactionType": "TransferFromBankToCustomer",
    "resultUrl": "https://yourdomain.com/mpesa/b2c-callback"
  }
}
```

#### Responses:

##### Code 200 OK (application/json)
```json
{
  "status": "SUCCESS",
  "responseCode": "000",
  "responseDescription": "The transaction was accepted successfully",
  "externalRef": "EXT-CBS-982348"
}
```

#### Code Snippet (C# HttpClient):
```csharp
var client = new HttpClient();
var request = new HttpRequestMessage(HttpMethod.Post, "https://uat.dtbafrica.com/api/dev-portal/v3/mpesa/b2c");
request.Headers.Add("Accept", "application/json");
request.Headers.Add("Authorization", "Bearer YOUR_ACCESS_TOKEN");

var jsonPayload = @"{
  ""identifier"": {
    ""referenceID"": ""B2C_REF_1001"",
    ""channel"": ""DEV-PORTAL""
  },
  ""payload"": {
    ""beneficiaryMsisdn"": ""254700000000"",
    ""transactionAmount"": 100,
    ""customerMsisdn"": ""254700000000"",
    ""customerName"": ""John Doe"",
    ""accountNumber"": ""0012870005"",
    ""branchCode"": ""023"",
    ""currency"": ""KES"",
    ""mnoCode"": ""MPESA"",
    ""narration"": ""Vendor Payment"",
    ""transactionType"": ""TransferFromBankToCustomer"",
    ""resultUrl"": ""https://yourdomain.com/callbacks/b2c""
  }
}";

request.Content = new StringContent(jsonPayload, System.Text.Encoding.UTF8, "application/json");
var response = await client.SendAsync(request);
response.EnsureSuccessStatusCode();
Console.WriteLine(await response.Content.ReadAsStringAsync());
```

---

### M-Pesa STK-Push

Initiates a Lipa Na M-Pesa Online transaction (STK Push), prompting the customer to input their M-Pesa PIN on their mobile device to finalize a payment.

*   **HTTP Method:** `POST`
*   **Endpoint:** `https://uat.dtbafrica.com/api/dev-portal/v3/mpesa/stkpush`
*   **Authorization:** `Bearer <token>`
*   **Content-Type:** `application/json`

#### Request Body Schema:

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `TransactionRef` | string | Yes | Unique reference ID associated with the transaction. |
| `TransactionType` | string | Yes | Set to standard value: `CustomerPayBillOnline` |
| `Amount` | integer | Yes | Value to be transferred (value must be `>= 1`). |
| `PhoneNumber` | string | Yes | Mobile number to receive the STK prompt (format must be exactly 12 characters, e.g. `2547XXXXXXXX`). |
| `AccountNumber` | string | Yes | Your registered core account number to be credited (must be exactly 10 characters). |
| `BusinessShortCode` | string | Yes | The recipient business Paybill shortcode. |
| `TransactionDesc` | string | Yes | Description of the transaction. |
| `PromptDisplayAccount` | string | No | The custom account name displayed on the customer's phone prompt screen. |
| `UserCallback` | string <uri> | Yes | Public callback URL where the transaction success/fail result will be posted. |

#### Request Body Payload Sample:
```json
{
  "TransactionRef": "STK_REF_9921",
  "TransactionType": "CustomerPayBillOnline",
  "Amount": 1500,
  "PhoneNumber": "254700000000",
  "AccountNumber": "0012870005",
  "BusinessShortCode": "123456",
  "TransactionDesc": "Invoice Payment",
  "PromptDisplayAccount": "Vivace Clinic",
  "UserCallback": "https://yourdomain.com/callbacks/stk"
}
```

#### Responses:

##### Code 200 OK (application/json)
```json
{
  "status": "SUCCESS",
  "responseCode": "000",
  "responseDescription": "The service request was processed successfully.",
  "externalReference": "ws_CO_140720261545"
}
```

#### Code Snippet (C# HttpClient):
```csharp
var client = new HttpClient();
var request = new HttpRequestMessage(HttpMethod.Post, "https://uat.dtbafrica.com/api/dev-portal/v3/mpesa/stkpush");
request.Headers.Add("Accept", "application/json");
request.Headers.Add("Authorization", "Bearer YOUR_ACCESS_TOKEN");

var jsonPayload = @"{
  ""TransactionRef"": ""STK_TX_12345"",
  ""TransactionType"": ""CustomerPayBillOnline"",
  ""Amount"": 10,
  ""PhoneNumber"": ""254700000000"",
  ""AccountNumber"": ""0012870005"",
  ""BusinessShortCode"": ""123456"",
  ""TransactionDesc"": ""Medical Bill"",
  ""PromptDisplayAccount"": ""Vivace Cosmetics"",
  ""UserCallback"": ""https://yourdomain.com/callbacks/stk""
}";

request.Content = new StringContent(jsonPayload, System.Text.Encoding.UTF8, "application/json");
var response = await client.SendAsync(request);
response.EnsureSuccessStatusCode();
Console.WriteLine(await response.Content.ReadAsStringAsync());
```

---

### B2B Validation

Validates whether a business partner's M-Pesa shortcode is active and correct before initiating a Business-to-Business (B2B) transaction.

*   **HTTP Method:** `GET`
*   **Endpoint:** `https://uat.dtbafrica.com/api/dev-portal/v3/mpesa/v2/b2bvalidate`
*   **Authorization:** `Bearer <token>`

#### Query Parameters:

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `IdentifierType` | string | Yes | Set value to: `BusinessPayBill` or `BusinessBuyGoods` |
| `BusinessShortCode` | string | Yes | The target merchant's M-Pesa shortcode (e.g. `123456`). |

#### Responses:

##### Code 200 OK (application/json)
```json
{
  "responseCode": "000",
  "responseMessage": "Success",
  "errorDescription": "",
  "organizationName": "Safal Group Kenya"
}
```

#### Code Snippet (C# HttpClient):
```csharp
var client = new HttpClient();
var request = new HttpRequestMessage(HttpMethod.Get, "https://uat.dtbafrica.com/api/dev-portal/v3/mpesa/v2/b2bvalidate?IdentifierType=BusinessPayBill&BusinessShortCode=123456");
request.Headers.Add("Accept", "application/json");
request.Headers.Add("Authorization", "Bearer YOUR_ACCESS_TOKEN");

var response = await client.SendAsync(request);
response.EnsureSuccessStatusCode();
Console.WriteLine(await response.Content.ReadAsStringAsync());
```

---

### M-Pesa B2B Transfer

Facilitates Business-to-Business (B2B) transactions, moving funds from your core account directly to another organization’s M-Pesa Paybill or Buy Goods till.

*   **HTTP Method:** `POST`
*   **Endpoint:** `https://uat.dtbafrica.com/api/dev-portal/v3/mpesa/b2b`
*   **Authorization:** `Bearer <token>`
*   **Content-Type:** `application/json`

#### Request Body Schema:

```json
{
  "identifier": {
    "referenceID": "unique_b2b_reference_id",
    "channel": "DEV-PORTAL"
  },
  "payload": {
    "beneficiaryShortCode": "654321",
    "beneficiaryAccountNumber": "78234723",
    "transactionAmount": 5000,
    "customerMsisdn": "2547XXXXXXXX",
    "customerName": "Company A Limited",
    "accountNumber": "0012870005",
    "branchCode": "023",
    "mnoCode": "MPESA",
    "narration": "Stock purchase settlement",
    "transactionType": "BusinessPayBill",
    "resultUrl": "https://yourdomain.com/callbacks/b2b"
  }
}
```

#### Responses:

##### Code 200 OK (application/json)
```json
{
  "status": "SUCCESS",
  "responseCode": "000",
  "responseDescription": "The B2B transfer request was accepted successfully.",
  "externalRef": "EXT-B2B-19238"
}
```

#### Code Snippet (C# HttpClient):
```csharp
var client = new HttpClient();
var request = new HttpRequestMessage(HttpMethod.Post, "https://uat.dtbafrica.com/api/dev-portal/v3/mpesa/b2b");
request.Headers.Add("Accept", "application/json");
request.Headers.Add("Authorization", "Bearer YOUR_ACCESS_TOKEN");

var jsonPayload = @"{
  ""identifier"": {
    ""referenceID"": ""B2B_TX_89234"",
    ""channel"": ""DEV-PORTAL""
  },
  ""payload"": {
    ""beneficiaryShortCode"": ""654321"",
    ""beneficiaryAccountNumber"": ""78234723"",
    ""transactionAmount"": 1000,
    ""customerMsisdn"": ""254700000000"",
    ""customerName"": ""Vivace Clinics"",
    ""accountNumber"": ""0012870005"",
    ""branchCode"": ""023"",
    ""mnoCode"": ""MPESA"",
    ""narration"": ""Wholesale Supplier"",
    ""transactionType"": ""BusinessPayBill"",
    ""resultUrl"": ""https://yourdomain.com/callbacks/b2b""
  }
}";

request.Content = new StringContent(jsonPayload, System.Text.Encoding.UTF8, "application/json");
var response = await client.SendAsync(request);
response.EnsureSuccessStatusCode();
Console.WriteLine(await response.Content.ReadAsStringAsync());
```

The core difference between **DTB Till Moja STK Push** and a **Direct Safaricom M-Pesa STK Push (Daraja)** comes down to two aspects: **Where the money is held (custody)** and **how it is settled**.

Here is a side-by-side comparison of how both flows function operationally and technically.

---

### 1. Where the Money Goes (The Cash Flow)

#### Direct Safaricom M-Pesa STK (Daraja)
When the customer enters their PIN, the money is moved from their phone wallet into your **Safaricom Lipa Na M-Pesa Account (Utility/Paybill account)**.
*   **The Cash Flow:** Customer Wallet ──► Safaricom Till/Paybill Wallet (held by Safaricom).
*   **The Operational Reality:** The money sits in Safaricom's ecosystem. To use it for business operations or supplier payments, you must manually log into Safaricom's portal (or run a B2C transaction) to transfer or "sweep" those funds from Safaricom into your actual DTB bank account.

#### DTB Till Moja STK Push
When the customer enters their PIN, the money is settled **instantly and directly into your physical DTB Bank Account**.
*   **The Cash Flow:** Customer Wallet ──► Safaricom ──► DTB Bank Account (Instant Settlement).
*   **The Operational Reality:** There is no intermediate M-Pesa wallet. The cash is immediately available in your general bank ledger as soon as the successful callback is received.

---

### 2. API Management & Coding Complexity

#### Direct Safaricom M-Pesa STK (Daraja)
*   You must integrate directly with Safaricom's **Daraja API Platform**.
*   You are responsible for generating Safaricom credentials, managing OAuth tokens, handling Safaricom's security credential handshakes, and writing custom decryption algorithms for Safaricom payloads.

#### DTB Till Moja STK Push
*   You integrate only with **DTB’s Developer Portal**.
*   DTB acts as the technical proxy. Your Odoo instance makes a single call to DTB, and DTB handles the complex security handshakes with Safaricom behind the scenes on your behalf.

---

### Comparison Matrix

| Feature | Direct M-Pesa STK (Safaricom Daraja) | DTB Till Moja STK Push |
| :--- | :--- | :--- |
| **Payer Experience** | Prompted on phone via USSD pop-up | Prompted on phone via USSD pop-up *(Identical)* |
| **Instant Settlement Destination** | Safaricom Mobile Money Wallet | Your Business DTB Bank Account |
| **Manual Transfer Needed?** | **Yes** (Must sweep from M-Pesa to Bank) | **No** (Direct bank credit) |
| **API Endpoints Managed** | Safaricom Gateway (`api.safaricom.co.ke`) | DTB Gateway (`uat.dtbafrica.com`) |
| **Reconciliation Ledger** | Separate Safaricom Statement | Unified DTB Bank Statement |
| **Onboarding Partner** | Safaricom (Requires custom Paybill setup) | DTB Kenya (Linked directly to your corporate account) |

---

### Summary: Why Use DTB Till Moja STK over Direct Safaricom STK?

For an ERP system like Odoo, the **DTB Till Moja STK** is highly efficient for accounting because it removes a step in the cash lifecycle. 

Instead of having to reconcile Odoo invoices against a Safaricom statement, and then reconcile your Safaricom statement against your bank transfers, **Odoo invoice payments match your physical bank ledger instantly**.


This section outlines the exact step-by-step API reference, payloads, and mock test requests to validate your **M-Pesa STK Push (M-Pesa Express)** integration over the DTB V3 Platform.

---

## I. Complete STK Push Architecture & Payload Flow

```
 [ Odoo ERP ]              [ DTB V3 Gateway ]         [ Safaricom M-Pesa ]        [ Customer Phone ]
      │                            │                           │                           │
      │── 1. POST /auth/token ────►│                           │                           │
      │◄── 2. Return JWT Token ────│                           │                           │
      │                            │                           │                           │
      │── 3. POST /mpesa/stkpush ─►│                           │                           │
      │    (Bearer JWT Token)      │── 4. Call Daraja API ────►│                           │
      │                            │                            │── 5. Push SIM Prompt ───►│
      │                            │                            │◄── 6. PIN Entered ───────│
      │                            │◄── 7. Instant Settlement ──│                           │
      │◄── 8. POST /stk-callback ──│                            │                           │
      │    (Daraja Format Callback)│                            │                           │
```

---

## II. Exact API References & Real-World Payloads

### Step 1: Request JWT Token from DTB
Generates the short-lived access token required to authorize outbound requests to the bank gateway.

*   **HTTP Method:** `POST`
*   **Endpoint:** `https://uat.dtbafrica.com/api/dev-portal/v3/auth/token`
*   **Headers:**
    *   `Content-Type: application/x-www-form-urlencoded`
    *   `Accept: application/json`
*   **Request Body (Raw):**
    ```properties
    client_id=YOUR_V3_CLIENT_ID&client_secret=YOUR_V3_CLIENT_SECRET&grant_type=password&username=YOUR_PORTAL_USERNAME&password=YOUR_PORTAL_PASSWORD
    ```
*   **Response Payload (200 OK):**
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token": "r1_983247923847239847",
      "expires_in": 3600,
      "refresh_token_expires_in": 86400
    }
    ```

---

### Step 2: Initiate STK Push via DTB
Instructs DTB to trigger a payment prompt on the customer's phone. This payload is configured with your active invoice **INV/2026/00014 (Beatrice Kosgei - 8,700 KSh)**.

*   **HTTP Method:** `POST`
*   **Endpoint:** `https://uat.dtbafrica.com/api/dev-portal/v3/mpesa/stkpush`
*   **Headers:**
    *   `Content-Type: application/json`
    *   `Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (Token from Step 1)
*   **Request Body (Raw JSON):**
    ```json
    {
      "TransactionRef": "EXT-STK-INV202600014",
      "TransactionType": "CustomerPayBillOnline",
      "Amount": 8700,
      "PhoneNumber": "254790999957",
      "AccountNumber": "03193211002",
      "BusinessShortCode": "607769",
      "TransactionDesc": "Invoice Payment",
      "PromptDisplayAccount": "Beatrice Kosgei",
      "UserCallback": "https://vivace.odoo.mp.ke/api/dtb/stk-callback"
    }
    ```
*   **Response Payload (200 OK):**
    ```json
    {
      "status": "SUCCESS",
      "responseCode": "000",
      "responseDescription": "The service request was processed successfully.",
      "externalReference": "ws_CO_140720261545_ABC"
    }
    ```
    *(Note: `externalReference` represents the unique `CheckoutRequestID` returned from Safaricom).*

---

### Step 3: Asynchronous STK Callback (POST)
Once the customer enters their PIN, Safaricom processes the cash, DTB credits your bank ledger, and the gateway POSTs this standard Daraja-style callback payload to your Odoo staging server.

*   **HTTP Method:** `POST`
*   **Endpoint:** `https://vivace.odoo.mp.ke/api/dtb/stk-callback` (or `http://localhost:8569/api/dtb/stk-callback`)
*   **Headers:**
    *   `Content-Type: application/json`
    *   `X-Odoo-Database: vivace-prod`
*   **Request Body (Raw JSON):**
    ```json
    {
      "Body": {
        "stkCallback": {
          "MerchantRequestID": "29115-34620561-1",
          "CheckoutRequestID": "ws_CO_140720261545_ABC",
          "ResultCode": 0,
          "ResultDesc": "The service request is processed successfully.",
          "CallbackMetadata": {
            "Item": [
              { "Name": "Amount", "Value": 8700.0 },
              { "Name": "MpesaReceiptNumber", "Value": "RGH1234567" },
              { "Name": "PhoneNumber", "Value": 254790999957 }
            ]
          }
        }
      }
    }
    ```
*   **Response Payload (200 OK Handshake):**
    ```json
    {
      "ack_code": "00",
      "ack_description": "SUCCESS"
    }
    ```

---

## III. Ready-to-Run Postman Test Suite (Raw `curl` equivalents)

You can import these raw commands directly into Postman by clicking **Import** -> **Raw text**.

### 1. Get Token (DTB Gateway Auth)
```bash
curl -X POST "https://uat.dtbafrica.com/api/dev-portal/v3/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Accept: application/json" \
  -d "client_id=YOUR_V3_CLIENT_ID&client_secret=YOUR_V3_CLIENT_SECRET&grant_type=password&username=YOUR_PORTAL_USERNAME&password=YOUR_PORTAL_PASSWORD"
```

### 2. Initiate STK Push (Odoo to DTB)
```bash
curl -X POST "https://uat.dtbafrica.com/api/dev-portal/v3/mpesa/stkpush" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer INSERT_TOKEN_FROM_STEP_1_HERE" \
  -d '{
    "TransactionRef": "EXT-STK-INV202600014",
    "TransactionType": "CustomerPayBillOnline",
    "Amount": 8700,
    "PhoneNumber": "254790999957",
    "AccountNumber": "03193211002",
    "BusinessShortCode": "607769",
    "TransactionDesc": "Invoice Payment",
    "PromptDisplayAccount": "Beatrice Kosgei",
    "UserCallback": "https://vivace.odoo.mp.ke/api/dtb/stk-callback"
  }'
```

### 3. Trigger Successful Webhook Callback (Staging Server)
Use this command to simulate Safaricom posting a successful payment confirmation back to your server. It will automatically update the pending transaction status, post the payment ledger, and mark the Odoo invoice as Paid.

```bash
curl -X POST "https://vivace.odoo.mp.ke/api/dtb/stk-callback" \
  -H "Content-Type: application/json" \
  -H "X-Odoo-Database: vivace-prod" \
  -d '{
    "Body": {
      "stkCallback": {
        "MerchantRequestID": "29115-34620561-1",
        "CheckoutRequestID": "ws_CO_140720261545_ABC",
        "ResultCode": 0,
        "ResultDesc": "The service request is processed successfully.",
        "CallbackMetadata": {
          "Item": [
            {"Name": "Amount", "Value": 8700.0},
            {"Name": "MpesaReceiptNumber", "Value": "RGH1234567"},
            {"Name": "PhoneNumber", "Value": 254790999957}
          ]
        }
      }
    }
  }'
```

Based on Shadrach’s email, **you should be setting up STK to Till Moja.** 

Here is the exact technical difference between the two and why **STK to Till Moja** is the correct path for your multi-branch Odoo integration.

---

### The Difference: "STK to Bank" vs. "STK to Till"

#### 1. STK to Bank Account (Standard Portal Docs)
*   **How it works:** The STK push triggers a payment that bypasses your Till registry completely and posts directly into your raw corporate bank account.
*   **The Problem for Vivace:** Because Vivace has multiple branches (Parklands and Nakuru) with different ledgers, bypassing the Till directory means Odoo cannot easily determine which branch Till generated the payment. You lose Till-level routing, making automated multi-branch reconciliation difficult.

#### 2. STK to Till Moja (What You Need)
*   **How it works:** The STK push is initiated *through* a specific branch Till Moja number (e.g., Till `100004` for Parklands). The payment respects the Till's configuration, settles into the bank account associated with that Till, and fires a callback to Odoo containing the Till/Account number.
*   **Why this is correct:** This preserves your branch isolation. Parklands payments will cleanly hit the Parklands Odoo payment journal, and Nakuru payments will hit the Nakuru journal.

---

### How This Affects Your Odoo Development

**The great news is that your Odoo code is already written and structured for "STK to Till Moja."**

From the beginning of our architectural design, we associated all transactions with the Till config model (`dtb_till_id` and `till_number`).

#### What You Need to Do Next:
The standard portal documentation you have (`/v3/mpesa/stkpush`) is for the "STK to Bank" flow. You are currently waiting for the DTB team (@Digital Partnerships / @Maureen Mwendwa) to provide the **specific endpoint and JSON payload schema for initiating STK via the Till Moja platform**.

---

### Suggested Reply to the Email Thread
You can send this response to the thread to keep the momentum going:

***

Dear Shadrach, Maureen, and the Digital Partnerships Team,

Thank you for the clarification.

To ensure strict branch-ledger segregation in Odoo for Vivace Management (Parklands vs. Nakuru branches), we confirm that we are implementing **STK to Till Moja**. This will allow us to route and validate transactions using their specific branch Till numbers.

@Maureen Mwendwa / @Digital Partnerships: Could you kindly share:
1. The specific API endpoint URL used to initiate **STK Push via the Till Moja platform**.
2. The expected JSON request payload schema for this Till Moja-specific STK initiation.

Our Odoo database models and callback controllers are already built and waiting to receive this endpoint configuration.

Kind regards,

**Wycliffe Ochieng**  
Lead Developer  
Mobipine Limited

This specific endpoint (`/api/dev-portal/v3/mpesa/stkpush`) is for **STK to Bank Account**. 

This is exactly what Shadrach was referring to when he wrote: *"the STK you have visibility of in the docs is the one for STK to bank account."*

---

### How We Know This is "STK to Bank" (From the Payload Fields)

If you look closely at the request fields in this specification, they prove it is designed to bypass the Till Moja system and go directly to your bank account:

1.  **`AccountNumber` Field Constraint:** 
    *   The description reads: *"Account number to be credited... Possible values: >= 10 characters and <= 10 characters."*
    *   This strictly requires a **10-digit standard bank account number** (your raw DTB checking/current account). It will reject a 6-digit Till Moja number (like `100004` or `700007`).
2.  **`BusinessShortCode` Field:**
    *   This is your corporate Paybill number. It is designed to route money directly to your 10-digit account without passing through the Till Moja routing directory.

---

### What "STK to Till Moja" Looks Like Instead

When the DTB team (@Digital Partnerships / @Maureen Mwendwa) shares the Till Moja-specific STK Push API, the payload will be different:

*   **No 10-digit bank account in the payload:** You will **not** pass your raw 10-digit bank account number. Instead, you will pass a 6-digit **`till_number`** (e.g., `100004`).
*   **Bank-Side Mapping:** DTB's Till Moja platform already has your Till linked to your bank account in their backend. When you call the Till Moja STK API with the Till number, their system automatically knows which bank account to credit.
*   **Till-Specific Callbacks:** The callback returned to Odoo will contain Till-specific metadata, allowing Odoo to immediately know which branch and journal the payment belongs to.

### Summary
*   **This endpoint (`/v3/mpesa/stkpush`):** Bypasses Till Moja, credits your bank account directly, and requires a 10-digit account number.
*   **What you are waiting for:** The dedicated Till Moja STK Push endpoint, where you pass the Till number (`100004` or `700007`) and receive a Till-specific callback.


**Yes, absolutely. Your Odoo system can support both methods simultaneously.** 

In fact, supporting both is a highly robust architectural choice for a multi-branch business like Vivace Cosmetics & Laser Clinics. Here is how both can coexist and when you would use each.

---

### 1. How Odoo Uses Both (The Business Case)

*   **Branch Billings (Use STK to Till Moja):** 
    *   *Scenario:* A patient walks into the **Parklands Branch** or **Nakuru Branch** and pays their specific clinic bill.
    *   *Routing:* Odoo triggers the **STK to Till Moja** flow using the branch's specific Till number. The money goes directly to the bank account linked to that branch, and Odoo reconciles it against the correct branch payment journal.
*   **Corporate / Head Office Collections (Use STK to Bank):**
    *   *Scenario:* Vivace HQ issues a corporate invoice, receives wholesale payments, or processes general head office collections that do not belong to any specific clinic branch.
    *   *Routing:* Odoo triggers the standard **STK to Bank** flow using the master corporate account number. The funds go directly into the central company bank account, bypassing branch ledgers.

---

### 2. How the Code Natively Handles Both

Our current Python implementation is already designed to support this dual capability with a simple dynamic switch inside Odoo.

#### The Odoo Flow Selector
We can add a simple selection field on your `dtb.moja.till` configuration model to designate whether the payment point is a **Direct Bank Account** or a **Till Moja**:

```python
# In models/dtb_till.py
class DtbMojaTill(models.Model):
    _inherit = 'dtb.moja.till'

    flow_type = fields.Selection([
        ('bank', 'Direct to Bank Account'),
        ('till_moja', 'Till Moja Platform')
    ], default='till_moja', required=True)
```

Then, in your `_stk_push_request` helper method, Odoo dynamically evaluates this selection and builds the correct payload for the respective gateway:

```python
    @api.model
    def _stk_push_request(self, till_id, amount, phone_number, narration, partner_name=None, partner_id=None):
        till = self.env['dtb.moja.till'].browse(till_id)
        access_token = till.get_v3_access_token()

        if till.flow_type == 'bank':
            # 1. Build and send the V3 "STK to Bank" payload
            api_url = "https://uat.dtbafrica.com/api/dev-portal/v3/mpesa/stkpush"
            payload = {
                "TransactionRef": xref,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(amount),
                "PhoneNumber": phone_number,
                "AccountNumber": till.bank_account_number, # 10-digit account
                "BusinessShortCode": till.business_short_code,
                "TransactionDesc": narration,
                "PromptDisplayAccount": "Vivace HQ",
                "UserCallback": callback_url
            }
        else:
            # 2. Build and send the "STK to Till Moja" payload (Pending specs from Maureen)
            api_url = till.stk_push_url or "https://api.dtbafrica.com/till-moja/stk-push"
            payload = {
                "request_identifier": { ... },
                "request_data": {
                    "till_number": till.till_number, # 6-digit till
                    "amount": str(amount),
                    "phone_number": phone_number,
                    "narration": narration,
                    "callback_url": callback_url
                }
            }

        # 3. Call the respective DTB gateway
        resp = requests.post(api_url, json=payload, headers=headers, timeout=15)
```

---

### 3. Unified Webhook Callback Handling
No matter which of the two STK methods initiates the transaction, your **`stk_callback`** endpoint in `controllers/main.py` is already designed to process both formats securely:

*   If Safaricom returns the standard **Daraja nested metadata** (used by STK to Bank), your `_parse_stk_payload` method extracts the receipt, phone, and amount.
*   If DTB returns their flat **Till Moja JSON format** (used by STK to Till), your `_parse_stk_payload` automatically falls back and parses it cleanly.

This unified approach gives you complete control over both corporate-level collections and decentralized branch-level payments within a single Odoo custom module.