terraform {
  required_version = ">= 1.6.0"

  backend "gcs" {
    bucket = "stoked-reality-496422-q8-week6-primary"
    prefix = "terraform/week7"
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

module "networking" {
  source = "./modules/networking"

  project_id       = var.project_id
  region           = var.region
  network_name     = var.network_name
  subnet_name      = var.subnet_name
  subnet_cidr      = var.subnet_cidr
  ssh_source_range = var.ssh_source_range
}
