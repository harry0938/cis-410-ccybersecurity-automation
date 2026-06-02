output "artifact_registry_repository" {
  description = "Artifact Registry repository resource name."
  value       = google_artifact_registry_repository.cis410_app.name
}

output "image" {
  description = "Container image deployed to Cloud Run."
  value       = var.image
}

output "service_name" {
  description = "Cloud Run service name."
  value       = google_cloud_run_v2_service.flask_app.name
}

output "service_url" {
  description = "Public Cloud Run HTTPS URL."
  value       = google_cloud_run_v2_service.flask_app.uri
}
