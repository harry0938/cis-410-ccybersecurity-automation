output "network_name" {
  description = "The VPC network name."
  value       = google_compute_network.vpc.name
}

output "subnet_name" {
  description = "The subnet name."
  value       = google_compute_subnetwork.public.name
}

output "subnet_cidr" {
  description = "The subnet CIDR range."
  value       = google_compute_subnetwork.public.ip_cidr_range
}

output "firewall_rule_names" {
  description = "The firewall rule names."
  value = [
    google_compute_firewall.allow_ssh.name,
    google_compute_firewall.allow_http.name,
    google_compute_firewall.allow_icmp.name
  ]
}
