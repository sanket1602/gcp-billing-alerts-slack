# gcp-billing-alerts-slack
A solution which sends periodic GCP Billing Alerts to Slack. You can customize alert frequency according to your needs.


Architecture Diagram =


<img width="1356" height="306" alt="image" src="https://github.com/user-attachments/assets/84d04621-cf2b-4413-b407-b2baf4d7d946" />


Flow =

1. A GCP Budget Alert is published to **Pub/Sub**
2. The **Cloud Function** is triggered
3. The message is decoded and parsed
4. **Firestore** is checked to see when the last alert was sent
5. If the last alert was sent less than 4 hours ago, the alert is skipped
6. Otherwise, a Slack notification is sent
7. Firestore is updated with the latest alert timestamp


Prerequisits = 

1. A GCP user account with Admin access.
2. Your Slack incoming webhook URL (Steps are here = https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks/)
3. Attention to detail :) 


Code Explaination =


**Dependencies**

````
import base64
import json
import requests
from datetime import datetime, timezone
import functions_framework
from google.cloud import firestore
````

**Dependency Purpose**

| Dependency               | Purpose                          |
| ------------------------ | -------------------------------- |
| `base64`                 | Decode Pub/Sub message payload   |
| `json`                   | Parse decoded JSON data          |
| `requests`               | Send HTTP POST requests to Slack |
| `datetime`               | Handle time-based throttling     |
| `functions_framework`    | Required for GCP Cloud Functions |
| `google-cloud-firestore` | Store alert timestamps           |




**Cloud Function Trigger**

````
@functions_framework.cloud_event
def budget_alert_to_slack(cloud_event):
````

* Uses CloudEvents (required for Pub/Sub triggers in Cloud Functions Gen 2)
* Automatically triggered when a Pub/Sub message is received



**Configuration** 

````
SLACK_WEBHOOK_URL = "YOUR-SLACK-WEBHOOK-URL"
MIN_HOURS_BETWEEN_ALERTS = 4
````


| Variable                   | Description                     |
| -------------------------- | ------------------------------- |
| `SLACK_WEBHOOK_URL`        | Slack Incoming Webhook URL      |
| `MIN_HOURS_BETWEEN_ALERTS` | Minimum time gap between alerts |



**Firestore Setup (Throttling Mechanism)**

````
db = firestore.Client(database='billing-db-slack')
doc_ref = db.collection("alerts").document("lastSent")
````
Firestore is used to store the timestamp of the last sent alert:
````
alerts/
 └── lastSent
     └── timestamp: <UTC datetime>
````
This ensures throttling works even if the function scales to multiple instances.





**Pub/Sub Message Decoding**

````
payload = json.loads(
    base64.b64decode(data).decode("utf-8")
)
````

**Example decoded payload:**

````
{
  "budgetDisplayName": "Monthly Budget",
  "costAmount": 4200,
  "budgetAmount": 5500,
  "currencyCode": "USD",
  "alertThresholdExceeded": 0.85
}
````



**Alert Throttling Logic**

````
diff_hours = (now - last_time).total_seconds() / 3600

if diff_hours < MIN_HOURS_BETWEEN_ALERTS:
    return "Throttled"
````

* Prevents repeated Slack notifications
* Uses Firestore as a shared state store
* Ensures only one alert every 4 hours








**Slack Notification Format**

````
message = (
    f"*GCP Budget Alert*\n"
    f"Budget: {payload.get('budgetDisplayName')}\n"
    f"Cost: {payload.get('costAmount')} {payload.get('currencyCode')}\n"
    f"Budget Amount: {payload.get('budgetAmount')} {payload.get('currencyCode')}\n"
    f"Threshold: {payload.get('alertThresholdExceeded')}"
)
````

**Example Slack Message**

````
GCP Budget Alert
Budget: Monthly Budget
Cost: 4200 USD
Budget Amount: 5500 USD
Threshold: 0.85
````





**Sending the Alert to Slack** 


````
resp = requests.post(
    SLACK_WEBHOOK_URL,
    json={"text": message}
)
````

* Uses Slack Incoming Webhooks
* Validates HTTP response
* Throws an exception if Slack returns a non-200 response




**Updating Firestore Timestamp**


````
doc_ref.set({"timestamp": now})
````

* Stores the time when the alert was sent
* Used for future throttling decisions



**Error Handling**


````
except Exception as e:
    print(f"Error in budget_alert_to_slack: {e}")
    raise
````

* Logs errors to Cloud Logging
* Ensures failed executions are visible in GCP










**Key Benefits**
* Prevents Slack alert spam
* Scales safely with Cloud Functions
* Centralized throttling via Firestore
* Stateless compute, stateful control
* Cost-aware notification system
