resource "openstack_fw_rule_v1" "bad_example" {
  name             = "my_rule"
  description      = "let anyone in"
  action           = "allow"
  protocol         = "tcp"
  destination_port = "22"
  enabled          = "true"
}

resource "openstack_fw_rule_v1" "bad_example2" {
  name                   = "my_rule"
  description            = "don't let just anyone in"
  action                 = "allow"
  protocol               = "tcp"
  destination_ip_address = "10.10.10.1"
  destination_port       = "22"
  enabled                = "true"
}

resource "openstack_fw_rule_v1" "good_example" {
  name                   = "my_rule"
  description            = "don't let just anyone in"
  action                 = "allow"
  protocol               = "tcp"
  destination_ip_address = "10.10.10.1"
  source_ip_address      = "10.10.10.2"
  destination_port       = "22"
  enabled                = "true"
}
