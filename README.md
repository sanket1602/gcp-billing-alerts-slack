# gcp-billing-alerts-slack
A solution which sends periodic GCP Billing Alerts to Slack. You can customize alert frequency according to your needs.

This project is WIP!

Architecture Diagram =


<img width="1319" height="194" alt="image" src="https://github.com/user-attachments/assets/a961228c-b594-4c5c-ba9f-d368ace13ea3" />


Flow -

1. Budget Alert is Triggered.
2. Budget Alert is sent to Cloud Pub/Sub topic.
3. Cloud Pub/Sub topic sends the alert to a Cloud Function.
4. Cloud Function stores the timpestamp of the alert in Firestore DB to avoid frequent alerts.
5. Cloud Function only sends alerts to Slack within the time which we configure.


