terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.40"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.30"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.13"
    }
  }

  # Remote state, locked in DynamoDB. One state key per environment so a
  # dev apply can never touch prod state. See variables.tf:environment.
  backend "s3" {
    bucket         = "pylon-infra-tfstate"
    key            = "pylon/${terraform.workspace}/cluster.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "pylon-infra-tflock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "pylon-infra"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

provider "kubernetes" {
  host                   = module.cluster.endpoint
  cluster_ca_certificate = base64decode(module.cluster.ca_cert)
  token                  = module.cluster.auth_token
}
