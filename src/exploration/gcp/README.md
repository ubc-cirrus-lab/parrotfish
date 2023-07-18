# Running Parrotfish with GCP Cloud Functions:
## Local environment: 
We should first authenticate with the user credentials:
```shell
gcloud auth application-default login
```
## Other environment:
We should create a service account and attach it to the application.

In order to enable cost calculation the user should activate the billing cloud api in GCP.