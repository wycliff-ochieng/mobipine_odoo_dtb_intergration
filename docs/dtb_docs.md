*   internal-services
    
    *   **get**GenerateTill
        
    *   **post**CreateTill
        
    *   **post**AuthorizeTill
        
    *   **get**QueryTill
        
    *   **put**UpdateTill
        
    *   **del**DeleteTill
        
    *   **get**EnbaleDisableTill
        
    *   **get**QueryTillReference
        
*   external-services
    

[Extio](https://extio.io/)

Till Moja Services (1.0.5)
==========================

DTB API Team: [support@dtbafrica.com](mailto:support@dtbafrica.com)License: [DTBK API License](https://developer.dtbafrica.com/license)[Terms of Service](https://developer.dtbafrica.com/terms/)

Till Moja APIs - Create/Update/Delete/Query Merchant Tills

internal-services
=================

Basic CRUD operations on the Till Moja services

GenerateTill
------------

Generate Till Number for creating a new Till

##### Authorizations:

(_bearerAuthApiKeyAuth_)

### Responses

**200**

Success Response

**400**

Invalid request data, error details availabe in response payload!

**401**

Access token/API Key is missing or invalid

**409**

Duplicate Message, Kindly ensure ''xref'' is unique for each request!

**500**

System error, error details availabe in response payload!

get/till-moja/generate-till

### Response samples

*   200
    

**Content type**application/jsontext/plainapplication/jsonCopyExpand allCollapse all{

*   }
    
    *   "trace\_id": "EXT-8B937BD5-02DA-4F92-9246-AB7237F81DE6",
        
    *   "response\_code": "000",
        
    *   "response\_description": "SUCCESS",
        
    *   "till\_number": 100002
        

}

CreateTill
----------

Create a Till

##### Authorizations:

(_bearerAuthApiKeyAuth_)

##### Request Body schema: application/jsonrequired

Request payload for Create Till

request\_identifierrequiredobject (RequestIdentifier)request\_datarequiredobject

### Responses

**200**

Success Response

**400**

Invalid request data, error details availabe in response payload!

**401**

Access token/API Key is missing or invalid

**409**

Duplicate Message, Kindly ensure ''xref'' is unique for each request!

**500**

System error, error details availabe in response payload!

post/till-moja/create-till

### Request samples

*   Payload
    

**Content type**application/jsonCopyExpand allCollapse all{

*   },
    
    *   "xref": "EXT4078BC719A934781",
        
    *   "user\_id": "API\_M247",
        
    *   "password": "qOw1EaF23xvf=",
        
    *   "channel": "MBS"
        
*   }
    
    *   "till\_generation": "MANUAL",
        
    *   "till\_number": "100004",
        
    *   "till\_name": "XYZ PVT LTD. TILL",
        
    *   "till\_mobile\_number": "254790999957",
        
    *   "till\_email\_adress": "TEST@EXTIO.IO",
        
    *   "account\_source": "CORE BANKING",
        
    *   "account\_id": "5029728002",
        
    *   "validation\_required": "Y",
        
    *   "validation\_mode": "EXTERNAL VALIDATION",
        
    *   "validation\_url": "[https://somedomain.org/till/reference/find/100002/082822001](https://somedomain.org/till/reference/find/100002/082822001)",
        
    *   "callback\_url": "[https://somedomain.org/payment/notification](https://somedomain.org/payment/notification)"
        

}

### Response samples

*   200
    

**Content type**application/jsonCopyExpand allCollapse all{

*   },
    
    *   "xref": "EXT4078BC719A934781",
        
    *   "user\_id": "API\_M247",
        
    *   "channel": "MBS"
        
*   }
    
    *   "trace\_id": "EXT-4F234127-FC8E-41DC-AAB2-4D1A00690E5A",
        
    *   "response\_code": "000",
        
    *   "response\_description": "SUCCESS",
        
    *   "till\_number": "100004"
        

}

AuthorizeTill
-------------

Authorize a Till

##### Authorizations:

(_bearerAuthApiKeyAuth_)

##### Request Body schema: application/jsonrequired

Request payload for Authorize Till

request\_identifierrequiredobject (RequestIdentifier)request\_datarequiredobject

### Responses

**200**

Success Response

**400**

Invalid request data, error details availabe in response payload!

**401**

Access token/API Key is missing or invalid

**409**

Duplicate Message, Kindly ensure ''xref'' is unique for each request!

**500**

System error, error details availabe in response payload!

post/till-moja/authorize-till

### Request samples

*   Payload
    

**Content type**application/jsonCopyExpand allCollapse all{

*   },
    
    *   "xref": "EXT4078BC7111162469",
        
    *   "user\_id": "API\_SYBN",
        
    *   "password": "2MBqO6bN8EG2no8IyVOGqw==",
        
    *   "channel": "MBS"
        
*   }
    
    *   "till\_number": "700007",
        
    *   "actor\_action": "APPROVED",
        
    *   "actor\_remarks": "This is for testing"
        

}

### Response samples

*   200
    

**Content type**application/jsonCopyExpand allCollapse all{

*   },
    
    *   "xref": "EXT4078BC7111162469",
        
    *   "user\_id": "API\_SYBN",
        
    *   "channel": "MBS"
        
*   }
    
    *   "trace\_id": "EXT-549B75FB-C908-432E-8C05-CA35E757A6C3",
        
    *   "response\_code": "000",
        
    *   "response\_description": "SUCCESS",
        
    *   "till\_number": "700007"
        

}

QueryTill
---------

Query Till number

##### Authorizations:

(_bearerAuthApiKeyAuth_)

##### path Parameters

tillNumberrequiredstring

Till number to be queried

### Responses

**200**

Success Response

**400**

Invalid request data, error details availabe in response payload!

**401**

Access token/API Key is missing or invalid

**409**

Duplicate Message, Kindly ensure ''xref'' is unique for each request!

**500**

System error, error details availabe in response payload!

get/till-moja/query-till/{tillNumber}

### Response samples

*   200
    

**Content type**application/jsontext/plainapplication/jsonCopyExpand allCollapse all{

*   }
    
    *   "trace\_id": "EXT-5C1C3931-DA1B-4C8E-814E-D5C0E27EC748",
        
    *   "response\_code": "000",
        
    *   "response\_description": "SUCCESS",
        
    *   "till\_data": {}
        

}

UpdateTill
----------

Update Till

##### Authorizations:

(_bearerAuthApiKeyAuth_)

##### Request Body schema: application/jsonrequired

Request payload for Update Till

request\_identifierrequiredobject (RequestIdentifier)request\_datarequiredobject

### Responses

**200**

Success Response

**400**

Invalid request data, error details availabe in response payload!

**401**

Access token/API Key is missing or invalid

**409**

Duplicate Message, Kindly ensure ''xref'' is unique for each request!

**500**

System error, error details availabe in response payload!

put/till-moja/update-till

### Request samples

*   Payload
    

**Content type**application/jsonCopyExpand allCollapse all{

*   },
    
    *   "xref": "EXT4078BC719A934781",
        
    *   "user\_id": "API\_M247",
        
    *   "password": "qOw1EaF23xvf=",
        
    *   "channel": "MBS"
        
*   }
    
    *   "till\_number": "100003",
        
    *   "till\_name": "ABC PVT LTD. TILL",
        
    *   "till\_mobile\_number": "254790999957",
        
    *   "till\_email\_adress": "TEST@EXTIO.IO",
        
    *   "account\_source": "CORE BANKING",
        
    *   "account\_id": "5029728001",
        
    *   "validation\_required": "Y",
        
    *   "validation\_mode": "INTERNAL VALIDATION"
        

}

### Response samples

*   200
    

**Content type**application/jsonCopyExpand allCollapse all{

*   },
    
    *   "xref": "EXT4078BC719A934781",
        
    *   "user\_id": "API\_M247",
        
    *   "channel": "MBS"
        
*   }
    
    *   "trace\_id": "EXT-CEA9FC52-A799-4FD2-97F5-12940B54F340",
        
    *   "response\_code": "000",
        
    *   "response\_description": "SUCCESS",
        
    *   "till\_number": "100003"
        

}

DeleteTill
----------

Delete a Till

##### Authorizations:

(_bearerAuthApiKeyAuth_)

##### path Parameters

userIdrequiredstring

User ID assigned to API consumer

tillNumberrequiredstring

Till number to be Deleted

### Responses

**200**

Success Response

**400**

Invalid request data, error details availabe in response payload!

**401**

Access token/API Key is missing or invalid

**409**

Duplicate Message, Kindly ensure ''xref'' is unique for each request!

**500**

System error, error details availabe in response payload!

delete/till-moja/delete-till/{userId}/{tillNumber}

### Response samples

*   200
    

**Content type**application/jsontext/plainapplication/jsonCopyExpand allCollapse all{

*   }
    
    *   "trace\_id": "EXT-F161C1BA-CFF7-4E08-A5CF-E7268AF2DACE",
        
    *   "response\_code": "000",
        
    *   "response\_description": "SUCCESS",
        
    *   "till\_number": "100003"
        

}

EnbaleDisableTill
-----------------

Enable or Disable a Till

##### Authorizations:

(_bearerAuthApiKeyAuth_)

##### path Parameters

userIdrequiredstring

User ID assigned to API consumer

tillNumberrequiredstring

Till number to be Enabled or Disabled

tillStatusrequiredstring

ACTIVE or BLOCKED

### Responses

**200**

Success Response

**400**

Invalid request data, error details availabe in response payload!

**401**

Access token/API Key is missing or invalid

**409**

Duplicate Message, Kindly ensure ''xref'' is unique for each request!

**500**

System error, error details availabe in response payload!

get/till-moja/enable-disable-till/{userId}/{tillNumber}/{tillStatus}

### Response samples

*   200
    

**Content type**application/jsontext/plainapplication/jsonCopyExpand allCollapse all{

*   }
    
    *   "trace\_id": "EXT-F161C1BA-CFF7-4E08-A5CF-E7268AF2DACE",
        
    *   "response\_code": "000",
        
    *   "response\_description": "SUCCESS",
        
    *   "till\_number": "100003"
        

}

QueryTillReference
------------------

Query Till Reference

##### Authorizations:

(_bearerAuthApiKeyAuth_)

##### path Parameters

tillNumberrequiredstring

Till number to be queried

referenceNumberrequiredstring

Reference number to be queried for the till

### Responses

**200**

Success Response

**400**

Invalid request data, error details availabe in response payload!

**401**

Access token/API Key is missing or invalid

**409**

Duplicate Message, Kindly ensure ''xref'' is unique for each request!

**500**

System error, error details availabe in response payload!

get/till-moja/query-reference/{tillNumber}/{referenceNumber}

### Response samples

*   200
    

**Content type**application/jsontext/plainapplication/jsonCopyExpand allCollapse all{

*   }
    
    *   "trace\_id": "EXT-72D0D443-0A56-4197-A215-CB294F21A818",
        
    *   "response\_code": "000",
        
    *   "response\_description": "SUCCESS",
        
    *   "till\_data": {}
        

}

external-services
=================

API Specification for 3rd parties to expose services related to Till Moja

QueryExternalTillReference
--------------------------

Query External Till Reference

##### Authorizations:

(_bearerAuthApiKeyAuth_)

##### path Parameters

tillNumberrequiredstring

Till number to be queried

referenceNumberrequiredstring

Reference number to be queried for the till

transactionAmountrequirednumber

Transaction amount to be validated

### Responses

**200**

Success Response

**400**

Invalid request data, error details availabe in response payload!

**404**

No Data found for provided input!

**500**

System error, error details availabe in response payload!

get/till-moja/query-external-reference/{tillNumber}/{referenceNumber}

### Response samples

*   200
    

**Content type**application/jsontext/plainapplication/jsonCopy{

*   "till\_number": "100003",
    
*   "reference\_id": "4671-208-114",
    
*   "value\_1": "John F. Kennedy",
    
*   "value\_2": "test",
    
*   "value\_3": "",
    
*   "value\_4": "",
    
*   "value\_5": ""
    

}

CallbackNotificationTill
------------------------

Payment Notification (Callback)

##### Request Body schema: application/jsonrequired

Request payload for Callback Notification

xrefrequiredstring = 32 characters

A Reference number that uniquely identifies this notification.

cbs\_referencerequiredstring = 16 characters

Core Banking Reference

cbs\_modulerequiredstring = 2 characters

Core Banking Module

account\_numberrequiredstring = 10 characters

Account number for which this notification is generated

branch\_coderequiredstring = 3 characters

3 digit Branch Code

currencyrequiredstring = 3 characters

3 letter Currency Code

transaction\_timerequiredstring = 17 characters

"Date and time of the transaction (YYYYMMDD HH:MM:SS)"

value\_daterequiredstring = 8 characters

Date when the transaction will be affected to the account (YYYYMMDD)

amountrequiredstring

Amount debited/credited as part of this transaction

reversal\_indicatorrequiredstringEnum: "y" "n"

Identifies if this transaction was a reversal

debit\_credit\_indicatorrequiredstringEnum: "D" "C"

Identifies if this is Debit or Credit on the account

exchange\_raterequiredstring

For a foreign currency transaction, applied exchange rate

financial\_yearrequiredstring = 6 characters

Financial year as per core banking

customer\_namerequiredstring \[ 3 .. 128 \] characters

Customer's Full Name

customer\_mobilerequiredstring = 12 characters

Customer's Mobile Number

narrationrequiredstring \[ 0 .. 256 \] characters

User input remarks for this transaction

### Responses

**200**

Success Response

**400**

Invalid request data, error details availabe in response payload!

**401**

Access token/API Key is missing or invalid

**409**

Duplicate Message, Kindly ensure ''xref'' is unique for each request!

**500**

System error, error details availabe in response payload!

post/till-moja/callback/notification

### Request samples

*   Payload
    

**Content type**application/jsonCopy{

*   "xref": "EXT-72D0D443-0A56-4197-A215-CB294F21A818",
    
*   "cbs\_reference": "110CDPO172380008",
    
*   "cbs\_module": "RT",
    
*   "account\_number": "0012870005",
    
*   "branch\_code": "023",
    
*   "currency": "KES",
    
*   "transaction\_time": "20170826 23:49:12",
    
*   "value\_date": "20170826",
    
*   "amount": "1500",
    
*   "reversal\_indicator": "n",
    
*   "debit\_credit\_indicator": "C",
    
*   "exchange\_rate": "1",
    
*   "financial\_year": "FY2017",
    
*   "customer\_name": "John Doe",
    
*   "customer\_mobile": "254700000000",
    
*   "narration": "User remarks"
    

}

### Response samples

*   200
    

**Content type**application/jsonCopy{

*   "xref": "EXT-72D0D443-0A56-4197-A215-CB294F21A818",
    
*   "user\_reference": "ORAXYZNRTV0001",
    
*   "ack\_code": "00",
    
*   "ack\_description": "SUCCESS"
    

}

*   internal-services
    
*   external-services
    

[Extio](https://extio.io/)

Till Moja Services (1.0.5)
==========================

DTB API Team: [support@dtbafrica.com](mailto:support@dtbafrica.com)License: [DTBK API License](https://developer.dtbafrica.com/license)[Terms of Service](https://developer.dtbafrica.com/terms/)

Till Moja APIs - Create/Update/Delete/Query Merchant Tills

internal-services
=================

Basic CRUD operations on the Till Moja services

GenerateTill
------------

Generate Till Number for creating a new Till

##### Authorizations:

(_bearerAuthApiKeyAuth_)

### Responses

**200**

Success Response

**400**

Invalid request data, error details availabe in response payload!

**401**

Access token/API Key is missing or invalid

**409**

Duplicate Message, Kindly ensure ''xref'' is unique for each request!

**500**

System error, error details availabe in response payload!

get/till-moja/generate-till

### Response samples

*   200
    

**Content type**application/jsontext/plainapplication/jsonCopyExpand allCollapse all{

*   }
    
    *   "trace\_id": "EXT-8B937BD5-02DA-4F92-9246-AB7237F81DE6",
        
    *   "response\_code": "000",
        
    *   "response\_description": "SUCCESS",
        
    *   "till\_number": 100002
        

}

CreateTill
----------

Create a Till

##### Authorizations:

(_bearerAuthApiKeyAuth_)

##### Request Body schema: application/jsonrequired

Request payload for Create Till

request\_identifierrequiredobject (RequestIdentifier)request\_datarequiredobject

### Responses

**200**

Success Response

**400**

Invalid request data, error details availabe in response payload!

**401**

Access token/API Key is missing or invalid

**409**

Duplicate Message, Kindly ensure ''xref'' is unique for each request!

**500**

System error, error details availabe in response payload!

post/till-moja/create-till

### Request samples

*   Payload
    

**Content type**application/jsonCopyExpand allCollapse all{

*   },
    
    *   "xref": "EXT4078BC719A934781",
        
    *   "user\_id": "API\_M247",
        
    *   "password": "qOw1EaF23xvf=",
        
    *   "channel": "MBS"
        
*   }
    
    *   "till\_generation": "MANUAL",
        
    *   "till\_number": "100004",
        
    *   "till\_name": "XYZ PVT LTD. TILL",
        
    *   "till\_mobile\_number": "254790999957",
        
    *   "till\_email\_adress": "TEST@EXTIO.IO",
        
    *   "account\_source": "CORE BANKING",
        
    *   "account\_id": "5029728002",
        
    *   "validation\_required": "Y",
        
    *   "validation\_mode": "EXTERNAL VALIDATION",
        
    *   "validation\_url": "[https://somedomain.org/till/reference/find/100002/082822001](https://somedomain.org/till/reference/find/100002/082822001)",
        
    *   "callback\_url": "[https://somedomain.org/payment/notification](https://somedomain.org/payment/notification)"
        

}

### Response samples

*   200
    

**Content type**application/jsonCopyExpand allCollapse all{

*   },
    
    *   "xref": "EXT4078BC719A934781",
        
    *   "user\_id": "API\_M247",
        
    *   "channel": "MBS"
        
*   }
    
    *   "trace\_id": "EXT-4F234127-FC8E-41DC-AAB2-4D1A00690E5A",
        
    *   "response\_code": "000",
        
    *   "response\_description": "SUCCESS",
        
    *   "till\_number": "100004"
        

}

AuthorizeTill
-------------

Authorize a Till

##### Authorizations:

(_bearerAuthApiKeyAuth_)

##### Request Body schema: application/jsonrequired

Request payload for Authorize Till

request\_identifierrequiredobject (RequestIdentifier)request\_datarequiredobject

### Responses

**200**

Success Response

**400**

Invalid request data, error details availabe in response payload!

**401**

Access token/API Key is missing or invalid

**409**

Duplicate Message, Kindly ensure ''xref'' is unique for each request!

**500**

System error, error details availabe in response payload!

post/till-moja/authorize-till

### Request samples

*   Payload
    

**Content type**application/jsonCopyExpand allCollapse all{

*   },
    
    *   "xref": "EXT4078BC7111162469",
        
    *   "user\_id": "API\_SYBN",
        
    *   "password": "2MBqO6bN8EG2no8IyVOGqw==",
        
    *   "channel": "MBS"
        
*   }
    
    *   "till\_number": "700007",
        
    *   "actor\_action": "APPROVED",
        
    *   "actor\_remarks": "This is for testing"
        

}

### Response samples

*   200
    

**Content type**application/jsonCopyExpand allCollapse all{

*   },
    
    *   "xref": "EXT4078BC7111162469",
        
    *   "user\_id": "API\_SYBN",
        
    *   "channel": "MBS"
        
*   }
    
    *   "trace\_id": "EXT-549B75FB-C908-432E-8C05-CA35E757A6C3",
        
    *   "response\_code": "000",
        
    *   "response\_description": "SUCCESS",
        
    *   "till\_number": "700007"
        

}

QueryTill
---------

Query Till number

##### Authorizations:

(_bearerAuthApiKeyAuth_)

##### path Parameters

tillNumberrequiredstring

Till number to be queried

### Responses

**200**

Success Response

**400**

Invalid request data, error details availabe in response payload!

**401**

Access token/API Key is missing or invalid

**409**

Duplicate Message, Kindly ensure ''xref'' is unique for each request!

**500**

System error, error details availabe in response payload!

get/till-moja/query-till/{tillNumber}

### Response samples

*   200
    

**Content type**application/jsontext/plainapplication/jsonCopyExpand allCollapse all{

*   }
    
    *   "trace\_id": "EXT-5C1C3931-DA1B-4C8E-814E-D5C0E27EC748",
        
    *   "response\_code": "000",
        
    *   "response\_description": "SUCCESS",
        
    *   "till\_data": {}
        

}

UpdateTill
----------

Update Till

##### Authorizations:

(_bearerAuthApiKeyAuth_)

##### Request Body schema: application/jsonrequired

Request payload for Update Till

request\_identifierrequiredobject (RequestIdentifier)request\_datarequiredobject

### Responses

**200**

Success Response

**400**

Invalid request data, error details availabe in response payload!

**401**

Access token/API Key is missing or invalid

**409**

Duplicate Message, Kindly ensure ''xref'' is unique for each request!

**500**

System error, error details availabe in response payload!

put/till-moja/update-till

### Request samples

*   Payload
    

**Content type**application/jsonCopyExpand allCollapse all{

*   },
    
    *   "xref": "EXT4078BC719A934781",
        
    *   "user\_id": "API\_M247",
        
    *   "password": "qOw1EaF23xvf=",
        
    *   "channel": "MBS"
        
*   }
    
    *   "till\_number": "100003",
        
    *   "till\_name": "ABC PVT LTD. TILL",
        
    *   "till\_mobile\_number": "254790999957",
        
    *   "till\_email\_adress": "TEST@EXTIO.IO",
        
    *   "account\_source": "CORE BANKING",
        
    *   "account\_id": "5029728001",
        
    *   "validation\_required": "Y",
        
    *   "validation\_mode": "INTERNAL VALIDATION"
        

}

### Response samples

*   200
    

**Content type**application/jsonCopyExpand allCollapse all{

*   },
    
    *   "xref": "EXT4078BC719A934781",
        
    *   "user\_id": "API\_M247",
        
    *   "channel": "MBS"
        
*   }
    
    *   "trace\_id": "EXT-CEA9FC52-A799-4FD2-97F5-12940B54F340",
        
    *   "response\_code": "000",
        
    *   "response\_description": "SUCCESS",
        
    *   "till\_number": "100003"
        

}

DeleteTill
----------

Delete a Till

##### Authorizations:

(_bearerAuthApiKeyAuth_)

##### path Parameters

userIdrequiredstring

User ID assigned to API consumer

tillNumberrequiredstring

Till number to be Deleted

### Responses

**200**

Success Response

**400**

Invalid request data, error details availabe in response payload!

**401**

Access token/API Key is missing or invalid

**409**

Duplicate Message, Kindly ensure ''xref'' is unique for each request!

**500**

System error, error details availabe in response payload!

delete/till-moja/delete-till/{userId}/{tillNumber}

### Response samples

*   200
    

**Content type**application/jsontext/plainapplication/jsonCopyExpand allCollapse all{

*   }
    
    *   "trace\_id": "EXT-F161C1BA-CFF7-4E08-A5CF-E7268AF2DACE",
        
    *   "response\_code": "000",
        
    *   "response\_description": "SUCCESS",
        
    *   "till\_number": "100003"
        

}

EnbaleDisableTill
-----------------

Enable or Disable a Till

##### Authorizations:

(_bearerAuthApiKeyAuth_)

##### path Parameters

userIdrequiredstring

User ID assigned to API consumer

tillNumberrequiredstring

Till number to be Enabled or Disabled

tillStatusrequiredstring

ACTIVE or BLOCKED

### Responses

**200**

Success Response

**400**

Invalid request data, error details availabe in response payload!

**401**

Access token/API Key is missing or invalid

**409**

Duplicate Message, Kindly ensure ''xref'' is unique for each request!

**500**

System error, error details availabe in response payload!

get/till-moja/enable-disable-till/{userId}/{tillNumber}/{tillStatus}

### Response samples

*   200
    

**Content type**application/jsontext/plainapplication/jsonCopyExpand allCollapse all{

*   }
    
    *   "trace\_id": "EXT-F161C1BA-CFF7-4E08-A5CF-E7268AF2DACE",
        
    *   "response\_code": "000",
        
    *   "response\_description": "SUCCESS",
        
    *   "till\_number": "100003"
        

}

QueryTillReference
------------------

Query Till Reference

##### Authorizations:

(_bearerAuthApiKeyAuth_)

##### path Parameters

tillNumberrequiredstring

Till number to be queried

referenceNumberrequiredstring

Reference number to be queried for the till

### Responses

**200**

Success Response

**400**

Invalid request data, error details availabe in response payload!

**401**

Access token/API Key is missing or invalid

**409**

Duplicate Message, Kindly ensure ''xref'' is unique for each request!

**500**

System error, error details availabe in response payload!

get/till-moja/query-reference/{tillNumber}/{referenceNumber}

### Response samples

*   200
    

**Content type**application/jsontext/plainapplication/jsonCopyExpand allCollapse all{

*   }
    
    *   "trace\_id": "EXT-72D0D443-0A56-4197-A215-CB294F21A818",
        
    *   "response\_code": "000",
        
    *   "response\_description": "SUCCESS",
        
    *   "till\_data": {}
        

}

external-services
=================

API Specification for 3rd parties to expose services related to Till Moja

QueryExternalTillReference
--------------------------

Query External Till Reference

##### Authorizations:

(_bearerAuthApiKeyAuth_)

##### path Parameters

tillNumberrequiredstring

Till number to be queried

referenceNumberrequiredstring

Reference number to be queried for the till

transactionAmountrequirednumber

Transaction amount to be validated

### Responses

**200**

Success Response

**400**

Invalid request data, error details availabe in response payload!

**404**

No Data found for provided input!

**500**

System error, error details availabe in response payload!

get/till-moja/query-external-reference/{tillNumber}/{referenceNumber}

### Response samples

*   200
    

**Content type**application/jsontext/plainapplication/jsonCopy{

*   "till\_number": "100003",
    
*   "reference\_id": "4671-208-114",
    
*   "value\_1": "John F. Kennedy",
    
*   "value\_2": "test",
    
*   "value\_3": "",
    
*   "value\_4": "",
    
*   "value\_5": ""
    

}

CallbackNotificationTill
------------------------

Payment Notification (Callback)

##### Request Body schema: application/jsonrequired

Request payload for Callback Notification

xrefrequiredstring = 32 characters

A Reference number that uniquely identifies this notification.

cbs\_referencerequiredstring = 16 characters

Core Banking Reference

cbs\_modulerequiredstring = 2 characters

Core Banking Module

account\_numberrequiredstring = 10 characters

Account number for which this notification is generated

branch\_coderequiredstring = 3 characters

3 digit Branch Code

currencyrequiredstring = 3 characters

3 letter Currency Code

transaction\_timerequiredstring = 17 characters

"Date and time of the transaction (YYYYMMDD HH:MM:SS)"

value\_daterequiredstring = 8 characters

Date when the transaction will be affected to the account (YYYYMMDD)

amountrequiredstring

Amount debited/credited as part of this transaction

reversal\_indicatorrequiredstringEnum: "y" "n"

Identifies if this transaction was a reversal

debit\_credit\_indicatorrequiredstringEnum: "D" "C"

Identifies if this is Debit or Credit on the account

exchange\_raterequiredstring

For a foreign currency transaction, applied exchange rate

financial\_yearrequiredstring = 6 characters

Financial year as per core banking

customer\_namerequiredstring \[ 3 .. 128 \] characters

Customer's Full Name

customer\_mobilerequiredstring = 12 characters

Customer's Mobile Number

narrationrequiredstring \[ 0 .. 256 \] characters

User input remarks for this transaction

### Responses

**200**

Success Response

**400**

Invalid request data, error details availabe in response payload!

**401**

Access token/API Key is missing or invalid

**409**

Duplicate Message, Kindly ensure ''xref'' is unique for each request!

**500**

System error, error details availabe in response payload!

post/till-moja/callback/notification

### Request samples

*   Payload
    

**Content type**application/jsonCopy{

*   "xref": "EXT-72D0D443-0A56-4197-A215-CB294F21A818",
    
*   "cbs\_reference": "110CDPO172380008",
    
*   "cbs\_module": "RT",
    
*   "account\_number": "0012870005",
    
*   "branch\_code": "023",
    
*   "currency": "KES",
    
*   "transaction\_time": "20170826 23:49:12",
    
*   "value\_date": "20170826",
    
*   "amount": "1500",
    
*   "reversal\_indicator": "n",
    
*   "debit\_credit\_indicator": "C",
    
*   "exchange\_rate": "1",
    
*   "financial\_year": "FY2017",
    
*   "customer\_name": "John Doe",
    
*   "customer\_mobile": "254700000000",
    
*   "narration": "User remarks"
    

}

### Response samples

*   200
    

**Content type**application/jsonCopy{

*   "xref": "EXT-72D0D443-0A56-4197-A215-CB294F21A818",
    
*   "user\_reference": "ORAXYZNRTV0001",
    
*   "ack\_code": "00",
    
*   "ack\_description": "SUCCESS"
    

}

*   internal-services
    
*   external-services
    

[Extio](https://extio.io/)

Till Moja Services (1.0.5)
==========================

DTB API Team: [support@dtbafrica.com](mailto:support@dtbafrica.com)License: [DTBK API License](https://developer.dtbafrica.com/license)[Terms of Service](https://developer.dtbafrica.com/terms/)

Till Moja APIs - Create/Update/Delete/Query Merchant Tills

internal-services
=================

Basic CRUD operations on the Till Moja services

GenerateTill
------------

Generate Till Number for creating a new Till

##### Authorizations:

(_bearerAuthApiKeyAuth_)

### Responses

**200**

Success Response

**400**

Invalid request data, error details availabe in response payload!

**401**

Access token/API Key is missing or invalid

**409**

Duplicate Message, Kindly ensure ''xref'' is unique for each request!

**500**

System error, error details availabe in response payload!

get/till-moja/generate-till

### Response samples

*   200
    

**Content type**application/jsontext/plainapplication/jsonCopyExpand allCollapse all{

*   }
    
    *   "trace\_id": "EXT-8B937BD5-02DA-4F92-9246-AB7237F81DE6",
        
    *   "response\_code": "000",
        
    *   "response\_description": "SUCCESS",
        
    *   "till\_number": 100002
        

}

CreateTill
----------

Create a Till

##### Authorizations:

(_bearerAuthApiKeyAuth_)

##### Request Body schema: application/jsonrequired

Request payload for Create Till

request\_identifierrequiredobject (RequestIdentifier)request\_datarequiredobject

### Responses

**200**

Success Response

**400**

Invalid request data, error details availabe in response payload!

**401**

Access token/API Key is missing or invalid

**409**

Duplicate Message, Kindly ensure ''xref'' is unique for each request!

**500**

System error, error details availabe in response payload!

post/till-moja/create-till

### Request samples

*   Payload
    

**Content type**application/jsonCopyExpand allCollapse all{

*   },
    
    *   "xref": "EXT4078BC719A934781",
        
    *   "user\_id": "API\_M247",
        
    *   "password": "qOw1EaF23xvf=",
        
    *   "channel": "MBS"
        
*   }
    
    *   "till\_generation": "MANUAL",
        
    *   "till\_number": "100004",
        
    *   "till\_name": "XYZ PVT LTD. TILL",
        
    *   "till\_mobile\_number": "254790999957",
        
    *   "till\_email\_adress": "TEST@EXTIO.IO",
        
    *   "account\_source": "CORE BANKING",
        
    *   "account\_id": "5029728002",
        
    *   "validation\_required": "Y",
        
    *   "validation\_mode": "EXTERNAL VALIDATION",
        
    *   "validation\_url": "[https://somedomain.org/till/reference/find/100002/082822001](https://somedomain.org/till/reference/find/100002/082822001)",
        
    *   "callback\_url": "[https://somedomain.org/payment/notification](https://somedomain.org/payment/notification)"
        

}

### Response samples

*   200
    

**Content type**application/jsonCopyExpand allCollapse all{

*   },
    
    *   "xref": "EXT4078BC719A934781",
        
    *   "user\_id": "API\_M247",
        
    *   "channel": "MBS"
        
*   }
    
    *   "trace\_id": "EXT-4F234127-FC8E-41DC-AAB2-4D1A00690E5A",
        
    *   "response\_code": "000",
        
    *   "response\_description": "SUCCESS",
        
    *   "till\_number": "100004"
        

}

AuthorizeTill
-------------

Authorize a Till

##### Authorizations:

(_bearerAuthApiKeyAuth_)

##### Request Body schema: application/jsonrequired

Request payload for Authorize Till

request\_identifierrequiredobject (RequestIdentifier)request\_datarequiredobject

### Responses

**200**

Success Response

**400**

Invalid request data, error details availabe in response payload!

**401**

Access token/API Key is missing or invalid

**409**

Duplicate Message, Kindly ensure ''xref'' is unique for each request!

**500**

System error, error details availabe in response payload!

post/till-moja/authorize-till

### Request samples

*   Payload
    

**Content type**application/jsonCopyExpand allCollapse all{

*   },
    
    *   "xref": "EXT4078BC7111162469",
        
    *   "user\_id": "API\_SYBN",
        
    *   "password": "2MBqO6bN8EG2no8IyVOGqw==",
        
    *   "channel": "MBS"
        
*   }
    
    *   "till\_number": "700007",
        
    *   "actor\_action": "APPROVED",
        
    *   "actor\_remarks": "This is for testing"
        

}

### Response samples

*   200
    

**Content type**application/jsonCopyExpand allCollapse all{

*   },
    
    *   "xref": "EXT4078BC7111162469",
        
    *   "user\_id": "API\_SYBN",
        
    *   "channel": "MBS"
        
*   }
    
    *   "trace\_id": "EXT-549B75FB-C908-432E-8C05-CA35E757A6C3",
        
    *   "response\_code": "000",
        
    *   "response\_description": "SUCCESS",
        
    *   "till\_number": "700007"
        

}

QueryTill
---------

Query Till number

##### Authorizations:

(_bearerAuthApiKeyAuth_)

##### path Parameters

tillNumberrequiredstring

Till number to be queried

### Responses

**200**

Success Response

**400**

Invalid request data, error details availabe in response payload!

**401**

Access token/API Key is missing or invalid

**409**

Duplicate Message, Kindly ensure ''xref'' is unique for each request!

**500**

System error, error details availabe in response payload!

get/till-moja/query-till/{tillNumber}

### Response samples

*   200
    

**Content type**application/jsontext/plainapplication/jsonCopyExpand allCollapse all{

*   }
    
    *   "trace\_id": "EXT-5C1C3931-DA1B-4C8E-814E-D5C0E27EC748",
        
    *   "response\_code": "000",
        
    *   "response\_description": "SUCCESS",
        
    *   "till\_data": {}
        

}

UpdateTill
----------

Update Till

##### Authorizations:

(_bearerAuthApiKeyAuth_)

##### Request Body schema: application/jsonrequired

Request payload for Update Till

request\_identifierrequiredobject (RequestIdentifier)request\_datarequiredobject

### Responses

**200**

Success Response

**400**

Invalid request data, error details availabe in response payload!

**401**

Access token/API Key is missing or invalid

**409**

Duplicate Message, Kindly ensure ''xref'' is unique for each request!

**500**

System error, error details availabe in response payload!

put/till-moja/update-till

### Request samples

*   Payload
    

**Content type**application/jsonCopyExpand allCollapse all{

*   },
    
    *   "xref": "EXT4078BC719A934781",
        
    *   "user\_id": "API\_M247",
        
    *   "password": "qOw1EaF23xvf=",
        
    *   "channel": "MBS"
        
*   }
    
    *   "till\_number": "100003",
        
    *   "till\_name": "ABC PVT LTD. TILL",
        
    *   "till\_mobile\_number": "254790999957",
        
    *   "till\_email\_adress": "TEST@EXTIO.IO",
        
    *   "account\_source": "CORE BANKING",
        
    *   "account\_id": "5029728001",
        
    *   "validation\_required": "Y",
        
    *   "validation\_mode": "INTERNAL VALIDATION"
        

}

### Response samples

*   200
    

**Content type**application/jsonCopyExpand allCollapse all{

*   },
    
    *   "xref": "EXT4078BC719A934781",
        
    *   "user\_id": "API\_M247",
        
    *   "channel": "MBS"
        
*   }
    
    *   "trace\_id": "EXT-CEA9FC52-A799-4FD2-97F5-12940B54F340",
        
    *   "response\_code": "000",
        
    *   "response\_description": "SUCCESS",
        
    *   "till\_number": "100003"
        

}

DeleteTill
----------

Delete a Till

##### Authorizations:

(_bearerAuthApiKeyAuth_)

##### path Parameters

userIdrequiredstring

User ID assigned to API consumer

tillNumberrequiredstring

Till number to be Deleted

### Responses

**200**

Success Response

**400**

Invalid request data, error details availabe in response payload!

**401**

Access token/API Key is missing or invalid

**409**

Duplicate Message, Kindly ensure ''xref'' is unique for each request!

**500**

System error, error details availabe in response payload!

delete/till-moja/delete-till/{userId}/{tillNumber}

### Response samples

*   200
    

**Content type**application/jsontext/plainapplication/jsonCopyExpand allCollapse all{

*   }
    
    *   "trace\_id": "EXT-F161C1BA-CFF7-4E08-A5CF-E7268AF2DACE",
        
    *   "response\_code": "000",
        
    *   "response\_description": "SUCCESS",
        
    *   "till\_number": "100003"
        

}

EnbaleDisableTill
-----------------

Enable or Disable a Till

##### Authorizations:

(_bearerAuthApiKeyAuth_)

##### path Parameters

userIdrequiredstring

User ID assigned to API consumer

tillNumberrequiredstring

Till number to be Enabled or Disabled

tillStatusrequiredstring

ACTIVE or BLOCKED

### Responses

**200**

Success Response

**400**

Invalid request data, error details availabe in response payload!

**401**

Access token/API Key is missing or invalid

**409**

Duplicate Message, Kindly ensure ''xref'' is unique for each request!

**500**

System error, error details availabe in response payload!

get/till-moja/enable-disable-till/{userId}/{tillNumber}/{tillStatus}

### Response samples

*   200
    

**Content type**application/jsontext/plainapplication/jsonCopyExpand allCollapse all{

*   }
    
    *   "trace\_id": "EXT-F161C1BA-CFF7-4E08-A5CF-E7268AF2DACE",
        
    *   "response\_code": "000",
        
    *   "response\_description": "SUCCESS",
        
    *   "till\_number": "100003"
        

}

QueryTillReference
------------------

Query Till Reference

##### Authorizations:

(_bearerAuthApiKeyAuth_)

##### path Parameters

tillNumberrequiredstring

Till number to be queried

referenceNumberrequiredstring

Reference number to be queried for the till

### Responses

**200**

Success Response

**400**

Invalid request data, error details availabe in response payload!

**401**

Access token/API Key is missing or invalid

**409**

Duplicate Message, Kindly ensure ''xref'' is unique for each request!

**500**

System error, error details availabe in response payload!

get/till-moja/query-reference/{tillNumber}/{referenceNumber}

### Response samples

*   200
    

**Content type**application/jsontext/plainapplication/jsonCopyExpand allCollapse all{

*   }
    
    *   "trace\_id": "EXT-72D0D443-0A56-4197-A215-CB294F21A818",
        
    *   "response\_code": "000",
        
    *   "response\_description": "SUCCESS",
        
    *   "till\_data": {}
        

}

external-services
=================

API Specification for 3rd parties to expose services related to Till Moja

QueryExternalTillReference
--------------------------

Query External Till Reference

##### Authorizations:

(_bearerAuthApiKeyAuth_)

##### path Parameters

tillNumberrequiredstring

Till number to be queried

referenceNumberrequiredstring

Reference number to be queried for the till

transactionAmountrequirednumber

Transaction amount to be validated

### Responses

**200**

Success Response

**400**

Invalid request data, error details availabe in response payload!

**404**

No Data found for provided input!

**500**

System error, error details availabe in response payload!

get/till-moja/query-external-reference/{tillNumber}/{referenceNumber}

### Response samples

*   200
    

**Content type**application/jsontext/plainapplication/jsonCopy{

*   "till\_number": "100003",
    
*   "reference\_id": "4671-208-114",
    
*   "value\_1": "John F. Kennedy",
    
*   "value\_2": "test",
    
*   "value\_3": "",
    
*   "value\_4": "",
    
*   "value\_5": ""
    

}

CallbackNotificationTill
------------------------

Payment Notification (Callback)

##### Request Body schema: application/jsonrequired

Request payload for Callback Notification

xrefrequiredstring = 32 characters

A Reference number that uniquely identifies this notification.

cbs\_referencerequiredstring = 16 characters

Core Banking Reference

cbs\_modulerequiredstring = 2 characters

Core Banking Module

account\_numberrequiredstring = 10 characters

Account number for which this notification is generated

branch\_coderequiredstring = 3 characters

3 digit Branch Code

currencyrequiredstring = 3 characters

3 letter Currency Code

transaction\_timerequiredstring = 17 characters

"Date and time of the transaction (YYYYMMDD HH:MM:SS)"

value\_daterequiredstring = 8 characters

Date when the transaction will be affected to the account (YYYYMMDD)

amountrequiredstring

Amount debited/credited as part of this transaction

reversal\_indicatorrequiredstringEnum: "y" "n"

Identifies if this transaction was a reversal

debit\_credit\_indicatorrequiredstringEnum: "D" "C"

Identifies if this is Debit or Credit on the account

exchange\_raterequiredstring

For a foreign currency transaction, applied exchange rate

financial\_yearrequiredstring = 6 characters

Financial year as per core banking

customer\_namerequiredstring \[ 3 .. 128 \] characters

Customer's Full Name

customer\_mobilerequiredstring = 12 characters

Customer's Mobile Number

narrationrequiredstring \[ 0 .. 256 \] characters

User input remarks for this transaction

### Responses

**200**

Success Response

**400**

Invalid request data, error details availabe in response payload!

**401**

Access token/API Key is missing or invalid

**409**

Duplicate Message, Kindly ensure ''xref'' is unique for each request!

**500**

System error, error details availabe in response payload!

post/till-moja/callback/notification

### Request samples

*   Payload
    

**Content type**application/jsonCopy{

*   "xref": "EXT-72D0D443-0A56-4197-A215-CB294F21A818",
    
*   "cbs\_reference": "110CDPO172380008",
    
*   "cbs\_module": "RT",
    
*   "account\_number": "0012870005",
    
*   "branch\_code": "023",
    
*   "currency": "KES",
    
*   "transaction\_time": "20170826 23:49:12",
    
*   "value\_date": "20170826",
    
*   "amount": "1500",
    
*   "reversal\_indicator": "n",
    
*   "debit\_credit\_indicator": "C",
    
*   "exchange\_rate": "1",
    
*   "financial\_year": "FY2017",
    
*   "customer\_name": "John Doe",
    
*   "customer\_mobile": "254700000000",
    
*   "narration": "User remarks"
    

}

### Response samples

*   200
    

**Content type**application/jsonCopy{

*   "xref": "EXT-72D0D443-0A56-4197-A215-CB294F21A818",
    
*   "user\_reference": "ORAXYZNRTV0001",
    
*   "ack\_code": "00",
    
*   "ack\_description": "SUCCESS"
    

}