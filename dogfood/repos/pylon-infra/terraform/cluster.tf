# The Kubernetes cluster and its managed node pools.
#
# INVARIANT: node pools are currently fixed-size. PI-215 (Stage 5)
# migrates prod to the cluster autoscaler; until then, capacity is set
# explicitly here and we over-provision to absorb spikes.

resource "aws_eks_cluster" "pylon" {
  name     = "pylon-${var.environment}"
  role_arn = aws_iam_role.cluster.arn
  version  = var.k8s_version

  vpc_config {
    subnet_ids              = var.private_subnet_ids
    endpoint_private_access = true
    endpoint_public_access  = var.environment != "prod"
  }

  # Spread across three AZs. Blast radius rule: one prod node pool per
  # change (.holdspeak/project.yaml:blast_radius_rule).
  kubernetes_network_config {
    service_ipv4_cidr = var.service_cidr
  }
}

# General-purpose on-demand pool. Steady-state workloads.
resource "aws_eks_node_group" "general" {
  cluster_name    = aws_eks_cluster.pylon.name
  node_group_name = "general"
  node_role_arn   = aws_iam_role.node.arn
  subnet_ids      = var.private_subnet_ids
  instance_types  = ["m6i.xlarge"]

  scaling_config {
    desired_size = var.general_desired_size
    min_size     = var.general_min_size
    max_size     = var.general_max_size
  }

  update_config {
    max_unavailable = 1
  }

  labels = {
    pool = "general"
  }
}

# Spot pool for bursty / batch work. Tainted so only opted-in pods land.
resource "aws_eks_node_group" "spot" {
  cluster_name    = aws_eks_cluster.pylon.name
  node_group_name = "spot"
  node_role_arn   = aws_iam_role.node.arn
  subnet_ids      = var.private_subnet_ids
  capacity_type   = "SPOT"
  instance_types  = ["m6i.large", "m5.large", "m5a.large"]

  scaling_config {
    desired_size = var.spot_desired_size
    min_size     = var.spot_min_size
    max_size     = var.spot_max_size
  }

  taint {
    key    = "workload"
    value  = "batch"
    effect = "NO_SCHEDULE"
  }

  labels = {
    pool = "spot"
  }
}
