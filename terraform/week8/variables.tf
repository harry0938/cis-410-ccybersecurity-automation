variable "project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "region" {
  description = "The GCP region."
  type        = string
  default     = "us-west1"
}

variable "repository_id" {
  description = "Artifact Registry Docker repository name."
  type        = string
  default     = "cis410-app"
}

variable "service_name" {
  description = "Cloud Run service name."
  type        = string
  default     = "cis410-flask-app"
}

variable "network_name" {
  description = "Existing VPC network name used by Cloud Run."
  type        = string
  default     = "cis410-vpc"
}

variable "subnet_name" {
  description = "Existing subnet name used by Cloud Run."
  type        = string
  default     = "cis410-vpc-public"
}

variable "image" {
  description = "Fully qualified Artifact Registry image URL to deploy."
  type        = string
}

variable "commit_sha" {
  description = "Git commit SHA deployed to Cloud Run."
  type        = string
  default     = "local"
}

variable "app_version" {
  description = "Application version displayed by the Flask app."
  type        = string
  default     = "2.0.0-cloudrun"
}
