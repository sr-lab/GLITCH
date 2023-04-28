resource "aws_elastic_beanstalk_environment" "tfenvtest" {
  dynamic "setting" {
    content {
      namespace = setting.value["namespace"]
    }
  }
}
