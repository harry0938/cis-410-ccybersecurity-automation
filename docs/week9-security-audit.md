# Week 9 Security Audit: IAM, Secret Manager, Logging & Monitoring

Project: `stoked-reality-496422-q8`
Service account audited: `cis410-deploy-sa@stoked-reality-496422-q8.iam.gserviceaccount.com`
Date: 2026-06-07

## 1. IAM Audit — Before / After

In Week 8 the deploy service account was given broad roles to get Cloud Run
working quickly. This week those bindings were audited and tightened to follow
least privilege. Two roles were reduced.

| Role | Week 8 (before) | Week 9 (after) | Why it changed |
| --- | --- | --- | --- |
| `roles/run.admin` | Project level | **Removed** | `run.admin` can manage every Cloud Run service *and* set IAM policy on them. The pipeline only needs to build and deploy revisions, so it was replaced with the narrower `roles/run.developer`. |
| `roles/run.developer` | — | **Project level (added)** | Allows the SA to deploy and update Cloud Run revisions without granting service-level IAM administration. |
| `roles/storage.objectAdmin` | Project level | **Removed** | A project-wide storage role let the SA read/write objects in *every* bucket. The pipeline only needs the Terraform state bucket. |
| `roles/storage.admin` | — | **Bucket level on `gs://stoked-reality-496422-q8-week6-primary` (added)** | The Terraform GCS backend (`terraform/week8/default.tfstate`) lives in this bucket. Scoping storage access to just this bucket removes access to all other buckets. |
| `roles/artifactregistry.admin` | Project level | Unchanged | Needed to push the `flask-app` image to Artifact Registry. |
| `roles/iam.serviceAccountUser` | Project level | Unchanged | Needed so the deploy SA can act as the Cloud Run runtime service account. |
| `roles/iam.serviceAccountTokenCreator` | Project level | Unchanged | Used by Workload Identity Federation token exchange. |
| `roles/compute.networkAdmin` | Project level | Unchanged | Cloud Run uses VPC egress (`network_interfaces` in Terraform). |

**Verification commands**

```bash
# Project-level roles for the deploy SA (after change)
gcloud projects get-iam-policy stoked-reality-496422-q8 \
  --flatten="bindings[].members" \
  --filter="bindings.members:cis410-deploy-sa@stoked-reality-496422-q8.iam.gserviceaccount.com" \
  --format="table(bindings.role)"

# Bucket-level role on the Terraform state bucket
gcloud storage buckets get-iam-policy gs://stoked-reality-496422-q8-week6-primary
```

After state confirmed: `roles/run.developer` present, `roles/run.admin` **absent**
at project level, `roles/storage.objectAdmin` **absent** at project level, and
`roles/storage.admin` present **only** on the `week6-primary` (tfstate) bucket.

> Note: This project authenticates GitHub Actions to GCP using **Workload
> Identity Federation** (OIDC), so there was never a long-lived service-account
> JSON key stored as a GitHub Secret to remove. The secret rotated to Secret
> Manager below is the application secret (`APP_SECRET`).

## 2. Secret Manager

A GCP Secret Manager secret now holds the application secret, accessed by Cloud
Run at runtime instead of being baked into the image or stored in CI/CD.

- Secret created: `flask-app-secret` (automatic replication), version `1` enabled.
- `roles/secretmanager.secretAccessor` granted to **both**:
  - `cis410-deploy-sa@stoked-reality-496422-q8.iam.gserviceaccount.com` (deploy SA)
  - `1063496881459-compute@developer.gserviceaccount.com` (Cloud Run runtime SA)
- Cloud Run service `cis410-flask-app` updated with env var `APP_SECRET`
  sourced from `flask-app-secret:latest` (not a plain value).
- Terraform (`terraform/week8/main.tf`) updated to inject the secret via
  `value_source.secret_key_ref` so the binding persists across deployments.

```bash
gcloud secrets create flask-app-secret --replication-policy=automatic --data-file=-
gcloud secrets add-iam-policy-binding flask-app-secret \
  --member="serviceAccount:cis410-deploy-sa@stoked-reality-496422-q8.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
gcloud secrets add-iam-policy-binding flask-app-secret \
  --member="serviceAccount:1063496881459-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
gcloud run services update cis410-flask-app --region=us-west1 \
  --update-secrets=APP_SECRET=flask-app-secret:latest
```

## 3. Cloud Logging

Logs Explorer shows request and application logs for the Cloud Run service.
Filter used (time range: Last 2 weeks):

```
resource.type="cloud_run_revision"
resource.labels.service_name="cis410-flask-app"
```

## 4. Log-Based Alert

Alert policy **`cis410-flask-app-errors`** (enabled) fires when the service emits
ERROR-or-higher log entries, notifying an email channel.

- Condition (matched-log) filter:
  ```
  resource.type="cloud_run_revision" AND
  resource.labels.service_name="cis410-flask-app" AND
  severity>=ERROR
  ```
- Notification channel: email (`CIS410 Email Alerts`).
- Rate limit: 1 notification / 300s.

## 5. Billing Budget

Budget **`cis410-monthly-budget`** created on billing account
`01BF40-E583A4-1C2595`, scoped to project `stoked-reality-496422-q8`.

- Amount: $10 USD / month.
- Alert thresholds: 50%, 90%, 100% of budget.

## Reflection Questions

**1. Why is replacing `roles/run.admin` with `roles/run.developer` an example of least privilege?**

`roles/run.admin` grants full control over every Cloud Run service in the
project, including the ability to change who can invoke a service via IAM. The
deploy pipeline only needs to build images and roll out new revisions, which
`roles/run.developer` already allows. Removing the admin role shrinks the blast
radius: if the deploy credentials were ever compromised, an attacker could not
re-open the service to the public or hijack its IAM bindings.

**2. Why is Google Secret Manager safer than keeping the value in CI/CD or in the image?**

Secret Manager stores the value encrypted at rest, versions it, and releases it
only to identities that hold `secretmanager.secretAccessor`, so access is
auditable and revocable in one place. Cloud Run reads it at runtime, which means
the secret never sits in the container image, the Git history, or a CI/CD
variable that many workflows can read. Rotating the secret is a new version
rather than a code change and redeploy.

**3. Why do a log-based alert and a billing budget matter for a capstone project?**

The error alert turns the service from something you check manually into
something that tells you when it breaks — ERROR logs page an email channel within
minutes instead of being noticed by a user. The budget does the same for cost:
an alert at 50/90/100% of $10 means a runaway resource or misconfiguration is
caught before it becomes a surprise bill. Together they are the minimum
observability and cost-safety net the capstone team needs before adding more
infrastructure in Weeks 10–11.
