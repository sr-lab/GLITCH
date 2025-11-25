resource "google_dns_managed_zone" "bad_example" {
}

resource "google_dns_managed_zone" "bad_example2" {
  dnssec_config {
    state = "off"
  }
}

resource "google_dns_managed_zone" "good_example" {
  dnssec_config {
    state = "on"
  }
}
