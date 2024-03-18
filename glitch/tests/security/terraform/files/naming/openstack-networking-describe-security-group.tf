resource "openstack_networking_secgroup_v2" "bad_example" {
}

resource "openstack_networking_secgroup_v2" "bad_example2" {
  description = ""
}

resource "openstack_networking_secgroup_v2" "good_example" {
  description = "don't let just anyone in"
}
