resource "aws_ecs_cluster" "bad_example" {
}

resource "aws_ecs_cluster" "bad_example2" {
  setting {
    name  = "containerInsights"
    value = "disabled"
  }
}

resource "aws_ecs_cluster" "bad_example3" {
  setting {
    name  = "containerInsights"
  }
}

resource "aws_ecs_cluster" "good_example" {
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}
