variable "project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "region" {
  description = "The GCP region."
  type        = string
}

variable "network_name" {
  description = "The VPC network name."
  type        = string
}

variable "subnet_name" {
  description = "The public subnet name."
  type        = string
}

variable "subnet_cidr" {
  description = "The subnet CIDR range."
  type        = string
}

variable "ssh_source_range" {
  description = "Your public IP address in CIDR format."
  type        = string
}
