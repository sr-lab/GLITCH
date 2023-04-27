data "google_dns_keys" "foo_dns_keys" {
   managed_zone = google_dns_managed_zone.foo.id
   zone_signing_keys {
      algorithm = "rsasha1"
   }
}
