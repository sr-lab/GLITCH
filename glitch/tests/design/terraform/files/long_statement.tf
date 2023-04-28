resource "openstack_compute_instance_v2" "example" {
  name            = "basic"
  image_id        = "ad091b52-742f-469e-8f3c-fd81cadf0743"
  flavor_id       = "3"
  security_groups = ["default"]
  user_data       = "#cloud-config\nhostname: instance_1.example.com\nfqdn: instance_1.exampleeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee.com"
}