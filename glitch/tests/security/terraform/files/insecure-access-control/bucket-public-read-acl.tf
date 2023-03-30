resource "digitalocean_spaces_bucket" "bad_example" {
  versioning {
    enabled = true
  }
}

resource "digitalocean_spaces_bucket" "bad_example2" {
  acl    = "public-read"
  versioning {
    enabled = true
  }
}

resource "digitalocean_spaces_bucket" "bad_example3" {
  acl    = "private"
  versioning {
    enabled = true
  }
}

resource "digitalocean_spaces_bucket_object" "index1" {
}

resource "digitalocean_spaces_bucket_object" "index2" {
  acl    = "public-read"
}


resource "digitalocean_spaces_bucket_object" "index3" {
  acl    = "private"
}
