resource "github_repository" "bad_example" {
  vulnerability_alerts = true
}

resource "github_repository" "bad_example" {
  visibility = "public-read"
  private = true
  vulnerability_alerts = true
}

resource "github_repository" "bad_example" {
  visibility = "private"
  private = true
  vulnerability_alerts = true
}

resource "github_repository" "bad_example" {
  private = false
  vulnerability_alerts = true
}

resource "github_repository" "bad_example" {
  private = true
  vulnerability_alerts = true
}

resource "github_repository" "bad_example" {
  visibility = "internal"
  vulnerability_alerts = true
}