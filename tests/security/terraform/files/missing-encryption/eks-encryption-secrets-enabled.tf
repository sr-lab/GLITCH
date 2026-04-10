resource "aws_eks_cluster" "bad_example" {
  enabled_cluster_log_types = ["api", "authenticator", "audit", "scheduler", "controllermanager"]
  vpc_config {
    endpoint_public_access = false
    public_access_cidrs = ["1.1.1.1"]
  }
}

resource "aws_eks_cluster" "bad_example2" {
  enabled_cluster_log_types = ["api", "authenticator", "audit", "scheduler", "controllermanager"]
  encryption_config {
    resources = [ "secrets" ]
  }
  vpc_config {
    endpoint_public_access = false
    public_access_cidrs = ["1.1.1.1"]
  }
}

resource "aws_eks_cluster" "bad_example3" {
  enabled_cluster_log_types = ["api", "authenticator", "audit", "scheduler", "controllermanager"]
  encryption_config {
    resources = [ "secret" ]
    provider {
      key_arn = var.kms_arn
    }
  }
  vpc_config {
    endpoint_public_access = false
    public_access_cidrs = ["1.1.1.1"]
  }
}

resource "aws_eks_cluster" "bad_example4" {
  enabled_cluster_log_types = ["api", "authenticator", "audit", "scheduler", "controllermanager"]
  encryption_config {
    provider {
      key_arn = var.kms_arn
    }
  }
  vpc_config {
    endpoint_public_access = false
    public_access_cidrs = ["1.1.1.1"]
  }
}

resource "aws_eks_cluster" "good_example" {
  enabled_cluster_log_types = ["api", "authenticator", "audit", "scheduler", "controllermanager"]
  encryption_config {
    resources = [ "secrets", "something"]
    provider {
      key_arn = var.kms_arn
    }
  }
  vpc_config {
    endpoint_public_access = false
    public_access_cidrs = ["1.1.1.1"]
  }
}
