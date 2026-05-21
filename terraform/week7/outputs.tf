output "network_name" {
  description = "The VPC network name."
  value       = module.networking.network_name
}

output "subnet_name" {
  description = "The subnet name."
  value       = module.networking.subnet_name
}

output "subnet_cidr" {
  description = "The subnet CIDR range."
  value       = module.networking.subnet_cidr
}

output "firewall_rule_names" {
  description = "The firewall rule names."
  value       = module.networking.firewall_rule_names
}
