import base64
import json
import requests
from datetime import datetime, timezone, timedelta
import functions_framework
from google.cloud import firestore

@functions_framework.cloud_event
def budget_alert_to_slack(cloud_event):
    """Triggered by a Pub/Sub message, sends budget alerts to Slack with 4-hour throttle."""

    SLACK_WEBHOOK_URL = "YOUR-SLACK-WEBHOOK-URL"
    MIN_HOURS_BETWEEN_ALERTS = 4 ## I have set it to 4 hours because of requirement, you're free to choose whatever freqquency you want 8) 

    db = firestore.Client(database='billing-db-slack')
    now = datetime.now(timezone.utc)
    doc_ref = db.collection("alerts").document("lastSent")

    try:
        # decode message
        if not cloud_event.data or "message" not in cloud_event.data:
            print("No message in event data.")
            return "No message"

        data = cloud_event.data["message"].get("data")
        if not data:
            print("No data in message.")
            return "No data"

        payload = json.loads(base64.b64decode(data).decode("utf-8"))
        print("Received payload:", payload)

        # read last alert time
        doc = doc_ref.get()
        if doc.exists:
            last_time = doc.to_dict().get("timestamp")
            if last_time:
                diff_hours = (now - last_time).total_seconds() / 3600
                print(f"Last alert {diff_hours:.2f} hours ago")

                if diff_hours < MIN_HOURS_BETWEEN_ALERTS:
                    print("Skipping Slack alert — throttled by Firestore window")
                    return "Throttled"

        # send to slack
        message = (
            f"*GCP Budget Alert*\n"
            f"Budget: {payload.get('budgetDisplayName')}\n"
            f"Cost: {payload.get('costAmount')} {payload.get('currencyCode')}\n"
            f"Budget Amount: {payload.get('budgetAmount')} {payload.get('currencyCode')}\n"
            f"Threshold: {payload.get('alertThresholdExceeded')}"
        )

        print("Sending alert to Slack")
        resp = requests.post(SLACK_WEBHOOK_URL, json={"text": message})
        print(f"Slack response: {resp.status_code}")

        if resp.status_code != 200:
            raise Exception(f"Slack webhook failed: {resp.text}")

        # update Firestore timestamp ---
        doc_ref.set({"timestamp": now})
        print("Firestore timestamp updated")

        return "Alert sent"

    except Exception as e:
        print(f"Error in budget_alert_to_slack: {e}")
        raise
