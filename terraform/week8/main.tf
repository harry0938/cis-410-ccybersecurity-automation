terraform {
  required_version = ">= 1.6.0"

  backend "gcs" {
    bucket = "stoked-reality-496422-q8-week6-primary"
    prefix = "terraform/week8"
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_project_service" "required_apis" {
  for_each = toset([
    "artifactregistry.googleapis.com",
    "run.googleapis.com",
    "iam.googleapis.com",
  ])

  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "cis410_app" {
  location      = var.region
  repository_id = var.repository_id
  description   = "CIS 410 Flask application images"
  format        = "DOCKER"

  depends_on = [google_project_service.required_apis]
}

resource "google_cloud_run_v2_service" "flask_app" {
  name                = var.service_name
  location            = var.region
  deletion_protection = false

  template {
    containers {
      image = var.image

      ports {
        container_port = 5000
      }

      env {
        name  = "ENVIRONMENT"
        value = "cloud-run"
      }

      env {
        name  = "APP_VERSION"
        value = var.app_version
      }

      env {
        name  = "COMMIT_SHA"
        value = var.commit_sha
      }

      # Week 9: inject application secret from Secret Manager at runtime
      # (not stored in CI/CD). Runtime SA has roles/secretmanager.secretAccessor.
      env {
        name = "APP_SECRET"
        value_source {
          secret_key_ref {
            secret  = "flask-app-secret"
            version = "latest"
          }
        }
      }
    }

    vpc_access {
      egress = "PRIVATE_RANGES_ONLY"

      network_interfaces {
        network    = var.network_name
        subnetwork = var.subnet_name
      }
    }
  }

  depends_on = [
    google_artifact_registry_repository.cis410_app,
    google_project_service.required_apis,
  ]
}

resource "google_cloud_run_service_iam_member" "public_invoker" {
  location = google_cloud_run_v2_service.flask_app.location
  service  = google_cloud_run_v2_service.flask_app.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
