# ---------------------------------------------------------------------------
# EcoChain Exchange - Terraform Provider Configuration
# Provisions the AWS cloud infrastructure for the platform:
#   VPC, EKS cluster, ECR repository, RDS PostgreSQL database
# ---------------------------------------------------------------------------

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Optional: remote state storage (recommended for team collaboration)
  # backend "s3" {
  #   bucket = "ecochain-terraform-state"
  #   key    = "ecochain/terraform.tfstate"
  #   region = "ap-south-1"
  # }
}

provider "aws" {
  region = var.aws_region
}
