# PetPlantr Multi-AZ Kubernetes Cluster IaC
# Story 3.3: Multi-AZ K8s cluster IaC

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
  }

  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "PetPlantr"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = "DevOps"
    }
  }
}

# VPC Configuration
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "petplantr-${var.environment}"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway     = true
  single_nat_gateway     = false
  enable_dns_hostnames   = true
  enable_dns_support     = true

  # Multi-AZ NAT gateways for high availability
  one_nat_gateway_per_az = true

  tags = {
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
  }

  public_subnet_tags = {
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
    "kubernetes.io/role/elb"                      = "1"
  }

  private_subnet_tags = {
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
    "kubernetes.io/role/internal-elb"             = "1"
  }
}

# EKS Cluster
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = local.cluster_name
  cluster_version = "1.28"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  # Multi-AZ deployment
  control_plane_subnet_ids = module.vpc.private_subnets

  # Extend cluster security group rules
  cluster_security_group_additional_rules = {
    ingress_nodes_ephemeral_ports_tcp = {
      description                = "Node groups to cluster API"
      protocol                   = "tcp"
      from_port                  = 1025
      to_port                    = 65535
      type                       = "ingress"
      source_node_security_group = true
    }
  }

  # Extend node-to-node security group rules
  node_security_group_additional_rules = {
    ingress_self_all = {
      description = "Node to node all ports/protocols"
      protocol    = "-1"
      from_port   = 0
      to_port     = 0
      type        = "ingress"
      self        = true
    }
    egress_all = {
      description = "Node all egress"
      protocol    = "-1"
      from_port   = 0
      to_port     = 0
      type        = "egress"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }

  # EKS Managed Node Group(s)
  eks_managed_node_group_defaults = {
    ami_type       = "AL2_x86_64"
    instance_types = ["m5.large", "m5.xlarge"]

    attach_cluster_primary_security_group = true
  }

  eks_managed_node_groups = {
    general = {
      name            = "general-purpose"
      instance_types   = ["m5.large"]
      min_size         = 3
      max_size         = 10
      desired_size     = 3
      capacity_type    = "ON_DEMAND"

      # Multi-AZ distribution
      availability_zones = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
      subnet_ids         = module.vpc.private_subnets

      tags = {
        "k8s.io/cluster-autoscaler/enabled" = "true"
        "k8s.io/cluster-autoscaler/${local.cluster_name}" = "owned"
      }
    }

    # Temporarily disabled GPU nodes due to account verification requirements
    # gpu = {
    #   name            = "gpu-nodes"
    #   instance_types   = ["g4dn.xlarge"]
    #   min_size         = 0
    #   max_size         = 5
    #   desired_size     = 1
    #   capacity_type    = "ON_DEMAND"
    #   ami_type         = "AL2_x86_64_GPU"
    #
    #   # GPU-specific taints and labels
    #   taints = [
    #     {
    #       key    = "nvidia.com/gpu"
    #       value  = "present"
    #       effect = "NO_SCHEDULE"
    #     }
    #   ]
    #
    #   labels = {
    #     "accelerator" = "nvidia-tesla-t4"
    #     "gpu"         = "true"
    #   }
    #
    #   tags = {
    #     "k8s.io/cluster-autoscaler/enabled" = "true"
    #     "k8s.io/cluster-autoscaler/${local.cluster_name}" = "owned"
    #   }
    # }
  }

  tags = {
    "Environment" = var.environment
  }
}

# RDS Database (if needed)
module "db" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  identifier = "petplantr-${var.environment}"

  # Multi-AZ for high availability
  multi_az               = true
  allocated_storage      = 20
  max_allocated_storage  = 100
  db_name                = "petplantr"
  username               = "petplantr"
  port                   = 5432

  # Engine configuration
  engine               = "postgres"
  engine_version       = "15.7"
  family               = "postgres15"
  major_engine_version = "15"
  instance_class       = "db.t3.micro"

  # Backup configuration
  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"

  # Security
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.petplantr.name

  # Monitoring
  monitoring_interval    = 60
  monitoring_role_name   = "rds-monitoring-role"
  create_monitoring_role = true

  tags = {
    "Environment" = var.environment
  }
}

# S3 Bucket for models and datasets
module "s3_bucket" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "~> 3.0"

  bucket = "petplantr-${var.environment}-models-${random_string.suffix.result}"

  # Versioning
  versioning = {
    enabled = true
  }

  # Server-side encryption
  server_side_encryption_configuration = {
    rule = {
      apply_server_side_encryption_by_default = {
        sse_algorithm = "AES256"
      }
    }
  }

  # Lifecycle configuration
  lifecycle_rule = [
    {
      id      = "models_lifecycle"
      enabled = true

      transition = [
        {
          days          = 30
          storage_class = "STANDARD_IA"
        },
        {
          days          = 90
          storage_class = "GLACIER"
        }
      ]

      expiration = {
        days = 365
      }
    }
  ]

  tags = {
    "Environment" = var.environment
  }
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "api_high_cpu" {
  alarm_name          = "petplantr-api-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "120"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors EC2 CPU utilization"

  tags = {
    "Environment" = var.environment
  }
}

# Application Load Balancer
module "alb" {
  source  = "terraform-aws-modules/alb/aws"
  version = "~> 8.0"

  name = "petplantr-${var.environment}"

  load_balancer_type = "application"

  vpc_id          = module.vpc.vpc_id
  subnets         = module.vpc.public_subnets
  security_groups = [aws_security_group.alb.id]

  # Security headers and SSL
  drop_invalid_header_fields = true
  enable_deletion_protection = true

  # Access logs
  access_logs = {
    bucket = module.s3_bucket.s3_bucket_id
    prefix = "alb-logs"
  }

  target_groups = [
    {
      name_prefix      = "petp-"
      backend_protocol = "HTTP"
      backend_port     = 80
      target_type      = "ip"

      health_check = {
        enabled             = true
        interval            = 30
        path                = "/health"
        port                = "traffic-port"
        healthy_threshold   = 3
        unhealthy_threshold = 3
        timeout             = 6
        protocol            = "HTTP"
        matcher             = "200-399"
      }
    }
  ]

  https_listeners = [
    {
      port               = 443
      protocol           = "HTTPS"
      certificate_arn    = aws_acm_certificate.petplantr.arn
      target_group_index = 0
    }
  ]

  http_tcp_listeners = [
    {
      port        = 80
      protocol    = "HTTP"
      action_type = "redirect"
      redirect = {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }
  ]

  tags = {
    "Environment" = var.environment
  }
}

# ArgoCD for GitOps
resource "helm_release" "argocd" {
  name       = "argocd"
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argo-cd"
  version    = "5.46.0"

  namespace        = "argocd"
  create_namespace = true

  values = [
    # Default ArgoCD configuration
    yamlencode({
      server: {
        service: {
          type: "LoadBalancer"
        }
      }
      configs: {
        secret: {
          argocdServerAdminPassword: "$2a$10$5vm8wXaS.5p9XcHqL3f9E.ZfPf4Q1QkQkQkQkQkQkQkQkQkQkQkQ"  # admin/admin
        }
      }
    })
  ]

  depends_on = [module.eks]
}

# Prometheus & Grafana monitoring stack
resource "helm_release" "kube_prometheus_stack" {
  name       = "monitoring"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  version    = "48.3.0"

  namespace        = "monitoring"
  create_namespace = true

  values = [
    # Default monitoring configuration
    yamlencode({
      grafana: {
        adminPassword: "admin"
        service: {
          type: "LoadBalancer"
        }
      }
      prometheus: {
        service: {
          type: "LoadBalancer"
        }
      }
    })
  ]

  depends_on = [module.eks]
}

# Cert Manager for SSL certificates
resource "helm_release" "cert_manager" {
  name       = "cert-manager"
  repository = "https://charts.jetstack.io"
  chart      = "cert-manager"
  version    = "v1.13.0"

  namespace        = "cert-manager"
  create_namespace = true

  set {
    name  = "installCRDs"
    value = "true"
  }

  depends_on = [module.eks]
}

# External DNS for automatic DNS management
resource "helm_release" "external_dns" {
  name       = "external-dns"
  repository = "https://kubernetes-sigs.github.io/external-dns"
  chart      = "external-dns"
  version    = "1.13.0"

  namespace        = "external-dns"
  create_namespace = true

  values = [
    # Default external-dns configuration
    yamlencode({
      provider: "aws"
      aws: {
        region: var.aws_region
      }
      domainFilters: [var.domain_name]
    })
  ]

  depends_on = [module.eks]
}

# Outputs
output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = module.eks.cluster_endpoint
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = module.eks.cluster_security_group_id
}

output "cluster_name" {
  description = "Kubernetes Cluster Name"
  value       = module.eks.cluster_name
}

output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = module.alb.lb_dns_name
}

output "database_endpoint" {
  description = "Database endpoint"
  value       = module.db.db_instance_address
}
