resource "google_project" "bad_example" {
}

resource "google_project" "bad_example2" {
  auto_create_network = true
}

resource "google_project" "good_example" {
  auto_create_network = false
}
