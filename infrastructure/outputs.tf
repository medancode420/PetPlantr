# PetPlantr Infrastructure Outputs
# Story 3.3: Multi-AZ K8s cluster IaC

# Note: Main outputs are defined in main.tf
# This file contains additional outputs for the infrastructure

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = module.eks.cluster_certificate_authority_data
}

output "cluster_oidc_issuer_url" {
  description = "The URL on the EKS cluster for the OpenID Connect identity provider"
  value       = module.eks.cluster_oidc_issuer_url
}

output "cluster_oidc_provider_arn" {
  description = "The ARN of the OIDC Provider"
  value       = module.eks.oidc_provider_arn
}

output "alb_zone_id" {
  description = "Zone ID of the load balancer"
  value       = module.alb.lb_zone_id
}

output "database_port" {
  description = "Database port"
  value       = module.db.db_instance_port
}

output "database_name" {
  description = "Database name"
  value       = module.db.db_instance_name
}

output "s3_bucket_name" {
  description = "S3 bucket name for models and datasets"
  value       = module.s3_bucket.s3_bucket_id
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN"
  value       = module.s3_bucket.s3_bucket_arn
}

output "s3_bucket_domain_name" {
  description = "S3 bucket domain name"
  value       = module.s3_bucket.s3_bucket_bucket_domain_name
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "VPC CIDR block"
  value       = module.vpc.vpc_cidr_block
}

output "private_subnets" {
  description = "List of private subnet IDs"
  value       = module.vpc.private_subnets
}

output "public_subnets" {
  description = "List of public subnet IDs"
  value       = module.vpc.public_subnets
}

output "nat_public_ips" {
  description = "List of public Elastic IPs created for AWS NAT Gateway"
  value       = module.vpc.nat_public_ips
}

output "argocd_admin_password" {
  description = "ArgoCD admin password"
  value       = helm_release.argocd.metadata[0].name != "" ? "admin" : null
  sensitive   = true
}

output "grafana_admin_password" {
  description = "Grafana admin password"
  value       = "admin"
  sensitive   = true
}

output "kubeconfig_command" {
  description = "Command to update kubeconfig"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${local.cluster_name}"
}

# Local values for outputs
locals {
  cluster_name = "petplantr-${var.environment}"
}
