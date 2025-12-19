# GCP Billing Alerts to Slack


GCP’s native billing alerts using Cloud Pub/Sub generate events every 30 minutes, which makes direct Slack integration noisy and impractical.

To solve this, I built an alerting pipeline using Cloud Pub/Sub, Cloud Functions, and Firestore. Billing events are ingested, aggregated, and rate-limited, and Slack notifications are sent only at configurable intervals. This approach reduces alert noise while retaining visibility into billing trends. The solution is simple to deploy and easily configurable based on operational needs.
<br/> 

# Architecture Diagram


<img width="1356" height="306" alt="image" src="https://github.com/user-attachments/assets/84d04621-cf2b-4413-b407-b2baf4d7d946" />
<br/> 
<br/> 

# Flow

1. A GCP Budget Alert is published to **Pub/Sub**
2. The **Cloud Function** is triggered
3. The message is decoded and parsed
4. **Firestore** is checked to see when the last alert was sent
5. If the last alert was sent less than 4 hours ago, the alert is skipped
6. Otherwise, a Slack notification is sent
7. Firestore is updated with the latest alert timestamp

<br/> 

# How to Use This Project

Follow the steps below to deploy and use the GCP Budget Alert → Slack notification system.
<br/>

**1. Prerequisites**

Ensure you have the following:

* A Google Cloud Project.
* Billing account linked to the project.
* Google Cloud CLI (gcloud) installed and authenticated.
* A Slack workspace with permission to create incoming webhooks.
<br/>

**2. Enable Required GCP APIs**
  
Enable the necessary APIs in your GCP project:
````
  gcloud services enable cloudfunctions.googleapis.com pubsub.googleapis.com firestore.googleapis.com cloudbuild.googleapis.com
````
<br/>

**3. Create a Slack Incoming Webhook**

1. Go to Slack → Settings → Apps
2. Search for Incoming Webhooks
3. Create a new webhook and select a channel
4. Copy the generated webhook URL
5. Replace the placeholder in the code:
````
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/XXX/YYY/ZZZ"
````
<br/>

**4. Create Firestore Database**

Create a Firestore database (Native mode):
````
gcloud firestore databases create --database=billing-db-slack --location=us-central1
````
> ℹ️ Firestore is used to store the timestamp of the last sent alert for throttling.
<br/>

**5. Create Pub/Sub Topic for Budget Alerts**

Create a Pub/Sub topic:
````
gcloud pubsub topics create budget-alerts
````
<br/>

**6. Configure GCP Budget Alert**

* Go to GCP Console → Billing → Budgets & alerts
* Create a new Budget
* Set the desired thresholds (e.g. 85%, 100%)
* Under Actions, select: 1) Send to Pub/Sub 2) Choose the topic: budget-alerts   
* Save the budget
<br/>

**7. Deploy the Cloud Function**

Deploy the Cloud Function (Gen 2):
````
gcloud functions deploy budget_alert_to_slack --gen2 --runtime=python311 --region=us-central1 --entry-point=budget_alert_to_slack --trigger-topic=budget-alerts --source=. --set-env-vars=GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project)
````
<br/>

**8. Grant Firestore Permissions**

Ensure the Cloud Function’s service account has access to Firestore:
````
gcloud projects add-iam-policy-binding $(gcloud config get-value project) --member="serviceAccount:$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')@cloudbuild.gserviceaccount.com" --role="roles/datastore.user"
````
<br/>

**9. Test the Setup**

Publish a Test Message:
````
gcloud pubsub topics publish budget-alerts --message='{"budgetDisplayName": "Test Budget","costAmount": 4200,"budgetAmount": 5500,"currencyCode": "USD","alertThresholdExceeded": 0.85}'
````
<br/>

#
# Code Explaination


**Dependencies**

````
import base64
import json
import requests
from datetime import datetime, timezone
import functions_framework
from google.cloud import firestore
````
<br/> 



**Dependency Purpose**

| Dependency               | Purpose                          |
| ------------------------ | -------------------------------- |
| `base64`                 | Decode Pub/Sub message payload   |
| `json`                   | Parse decoded JSON data          |
| `requests`               | Send HTTP POST requests to Slack |
| `datetime`               | Handle time-based throttling     |
| `functions_framework`    | Required for GCP Cloud Functions |
| `google-cloud-firestore` | Store alert timestamps           |


<br/> 


**Cloud Function Trigger**

````
@functions_framework.cloud_event
def budget_alert_to_slack(cloud_event):
````

* Uses CloudEvents (required for Pub/Sub triggers in Cloud Functions Gen 2)
* Automatically triggered when a Pub/Sub message is received

<br/> 


**Configuration** 

````
SLACK_WEBHOOK_URL = "YOUR-SLACK-WEBHOOK-URL"
MIN_HOURS_BETWEEN_ALERTS = 4
````


| Variable                   | Description                     |
| -------------------------- | ------------------------------- |
| `SLACK_WEBHOOK_URL`        | Slack Incoming Webhook URL      |
| `MIN_HOURS_BETWEEN_ALERTS` | Minimum time gap between alerts |

<br/> 


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


<br/> 



**Pub/Sub Message Decoding**

````
payload = json.loads(
    base64.b64decode(data).decode("utf-8")
)
````
<br/> 

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

<br/> 


**Alert Throttling Logic**

````
diff_hours = (now - last_time).total_seconds() / 3600

if diff_hours < MIN_HOURS_BETWEEN_ALERTS:
    return "Throttled"
````

* Prevents repeated Slack notifications
* Uses Firestore as a shared state store
* Ensures only one alert every 4 hours




<br/> 
 


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
<br/> 

**Example Slack Message**

````
GCP Budget Alert
Budget: Monthly Budget
Cost: 4200 USD
Budget Amount: 5500 USD
Threshold: 0.85
````

<br/> 




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


<br/> 


**Updating Firestore Timestamp**


````
doc_ref.set({"timestamp": now})
````

* Stores the time when the alert was sent
* Used for future throttling decisions

<br/> 


**Error Handling**


````
except Exception as e:
    print(f"Error in budget_alert_to_slack: {e}")
    raise
````

* Logs errors to Cloud Logging
* Ensures failed executions are visible in GCP


<br/> 
<br/> 



# Key Benefits
* Prevents Slack alert spam
* Scales safely with Cloud Functions
* Centralized throttling via Firestore
* Stateless compute, stateful control
* Cost-aware notification system
# 
