resource "aws_ecs_task_definition" "bad_example" {
  family                = "service"
  container_definitions = file("task-definitions/service.json")

  volume {
    name = "service-storage"

    efs_volume_configuration {
      file_system_id          = aws_efs_file_system.fs.id
      root_directory          = "/opt/data"
      authorization_config {
        access_point_id = aws_efs_access_point.test.id
        iam             = "ENABLED"
      }
    }
  }
}

resource "aws_ecs_task_definition" "bad_example2" {
  family                = "service"
  container_definitions = file("task-definitions/service.json")

  volume {
    name = "service-storage"

    efs_volume_configuration {
      file_system_id          = aws_efs_file_system.fs.id
      root_directory          = "/opt/data"
      transit_encryption      = "DISABLED"
      authorization_config {
        access_point_id = aws_efs_access_point.test.id
        iam             = "ENABLED"
      }
    }
  }
}

resource "aws_ecs_task_definition" "good_example" {
  family                = "service"
  container_definitions = file("task-definitions/service.json")

  volume {
    name = "service-storage"

    efs_volume_configuration {
      file_system_id          = aws_efs_file_system.fs.id
      root_directory          = "/opt/data"
      transit_encryption      = "ENABLED"
      authorization_config {
        access_point_id = aws_efs_access_point.test.id
        iam             = "ENABLED"
      }
    }
  }
}

resource "aws_ecs_task_definition" "good_example2" {
  family                = "service"
  container_definitions = file("task-definitions/service.json")

  volume {
    name = "service-storage"
  }
}
