# gcp-billing-alerts-slack
A solution which sends periodic GCP Billing Alerts to Slack. You can customize alert frequency according to your needs.

This project is WIP!

Architecture Diagram =


<img width="1356" height="306" alt="image" src="https://github.com/user-attachments/assets/84d04621-cf2b-4413-b407-b2baf4d7d946" />


Flow =

1. Budget Alert is Triggered.
2. Budget Alert is sent to Cloud Pub/Sub topic.
3. Cloud Pub/Sub topic sends the alert to a Cloud Function.
4. Cloud Function stores the timpestamp of the alert in Firestore DB to avoid frequent alerts.
5. Cloud Function only sends alerts to Slack after comparing it with timestamp stored in DB.


Prerequisits = 

1. A GCP user account with Admin access.
2. Your Slack incoming webhook URL (Steps are here = https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks/)
3. Attention to detail :) 


Code Explaination =

