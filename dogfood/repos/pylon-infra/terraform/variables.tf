# Per-environment inputs. Bound by tfvars files (one per environment):
# env/dev.tfvars, env/staging.tfvars, env/prod.tfvars.

variable "environment" {
  description = "Target environment: dev | staging | prod."
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}

variable "region" {
  description = "AWS region for the estate."
  type        = string
  default     = "eu-west-1"
}

variable "k8s_version" {
  description = "Kubernetes control-plane version."
  type        = string
  default     = "1.29"
}

variable "private_subnet_ids" {
  description = "Private subnets (one per AZ, three AZs)."
  type        = list(string)
}

variable "service_cidr" {
  description = "Cluster service IPv4 CIDR."
  type        = string
  default     = "172.20.0.0/16"
}

# --- general pool sizing ---
variable "general_desired_size" {
  type    = number
  default = 6
}

variable "general_min_size" {
  type    = number
  default = 3
}

variable "general_max_size" {
  type    = number
  default = 12
}

# --- spot pool sizing ---
variable "spot_desired_size" {
  type    = number
  default = 4
}

variable "spot_min_size" {
  type    = number
  default = 0
}

variable "spot_max_size" {
  type    = number
  default = 20
}
