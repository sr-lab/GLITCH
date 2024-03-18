resource "openstack_compute_instance_v2" "bad_example" {
  admin_pass      = "N0tSoS3cretP4ssw0rd"
}

resource "openstack_compute_instance_v2" "good_example" {
  key_pair        = "my_key_pair_name"
}
