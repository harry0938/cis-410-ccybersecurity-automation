variable "project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "region" {
  description = "The GCP region."
  type        = string
  default     = "us-west1"
}

variable "network_name" {
  description = "The VPC network name."
  type        = string
  default     = "cis410-vpc"
}

variable "subnet_name" {
  description = "The public subnet name."
  type        = string
  default     = "cis410-vpc-public"
}

variable "subnet_cidr" {
  description = "The subnet CIDR range."
  type        = string
  default     = "10.0.1.0/24"
}

variable "ssh_source_range" {
  description = "Your public IP address in CIDR format, such as x.x.x.x/32."
  type        = string
}
