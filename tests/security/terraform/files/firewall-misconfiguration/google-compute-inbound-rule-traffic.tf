resource "google_compute_firewall" "bad_example" {
  allow {
    protocol = "icmp"
  }
  destination_ranges = ["1.2.3.4/32"]
}

resource "google_compute_firewall" "good_example" {
  allow {
    protocol = "icmp"
  }
  source_ranges = ["1.2.3.4/32"]
  destination_ranges = ["1.2.3.4/32"]
}
