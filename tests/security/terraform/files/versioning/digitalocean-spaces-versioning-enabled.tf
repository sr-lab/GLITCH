resource "digitalocean_spaces_bucket" "bad_example" {
  acl = "private"
}

resource "digitalocean_spaces_bucket" "bad_example2" {
  versioning {
    enabled = false
  }

  acl = "private"
}

resource "digitalocean_spaces_bucket" "good_example" {
  versioning {
    enabled = true
  }

  acl = "private"
}
