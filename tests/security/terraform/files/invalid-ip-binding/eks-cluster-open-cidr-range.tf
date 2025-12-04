resource "aws_eks_cluster" "bad_example2" {
  enabled_cluster_log_types = ["api", "authenticator", "audit", "scheduler", "controllermanager"]
  encryption_config {
    resources = ["secrets"]
    provider {
      key_arn = "something"
    }
  }
  vpc_config {
      endpoint_public_access = false
      public_access_cidrs = ["0.0.0.0/8"]
  }
}

resource "aws_eks_cluster" "good_example" {
  enabled_cluster_log_types = ["api", "authenticator", "audit", "scheduler", "controllermanager"]
  encryption_config {
    resources = ["secrets"]
    provider {
      key_arn = "something"
    }
  }
  vpc_config {
      endpoint_public_access = false
      public_access_cidrs = ["10.2.0.0/8"]
  }
}