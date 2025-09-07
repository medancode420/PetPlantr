# Security Groups
resource "aws_security_group" "alb" {
  name_prefix = "petplantr-alb-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "petplantr-alb-sg"
  }
}

resource "aws_security_group" "rds" {
  name_prefix = "petplantr-rds-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description     = "PostgreSQL"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [module.eks.node_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "petplantr-rds-sg"
  }
}

# DB Subnet Group
resource "aws_db_subnet_group" "petplantr" {
  name       = "petplantr-${var.environment}"
  subnet_ids = module.vpc.private_subnets

  tags = {
    Name = "petplantr-db-subnet-group"
  }
}

# ACM Certificate
resource "aws_acm_certificate" "petplantr" {
  domain_name       = var.domain_name
  validation_method = "DNS"

  subject_alternative_names = [
    "*.${var.domain_name}"
  ]

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "petplantr-ssl-cert"
  }
}

# SNS Topic for alerts
resource "aws_sns_topic" "petplantr_alerts" {
  name = "petplantr-${var.environment}-alerts"

  tags = {
    Name = "petplantr-alerts"
  }
}

# Random suffix for S3 bucket
resource "random_string" "suffix" {
  length  = 8
  lower   = true
  upper   = false
  numeric = true
  special = false
}
