locals {
  instance_ids = concat(aws_instance.blue.*.id, aws_instance.green.*.id)
}

locals {
  labels1 = ["default", {yes = "yes"}, "hello"]

  common_tags = {
    Service = local.service_name
    Owner   = local.owner
  }
}
