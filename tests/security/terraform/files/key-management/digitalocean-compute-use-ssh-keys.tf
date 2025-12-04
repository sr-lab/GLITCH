resource "digitalocean_droplet" "bad_example" {
  image    = "ubuntu-18-04-x64"
  name     = "web-1"
  region   = "nyc2"
  size     = "s-1vcpu-1gb"
}

resource "digitalocean_droplet" "good_example" {
  image    = "ubuntu-18-04-x64"
  name     = "web-1"
  region   = "nyc2"
  size     = "s-1vcpu-1gb"
  ssh_keys = [1234]
}
