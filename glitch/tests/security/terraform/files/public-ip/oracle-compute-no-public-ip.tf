resource "opc_compute_ip_address_reservation" "bad_example" {
  name            = "my-ip-address"
  ip_address_pool = "public-ippool"
}

resource "opc_compute_ip_address_reservation" "good_example" {
  name            = "my-ip-address"
  ip_address_pool = "cloud-ippool"
}
