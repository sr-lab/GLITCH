resource "google_organization_iam_binding" "bad_example" {
  org_id  = "org-123"
  role    = "roles/iam.serviceAccountUser"
}

resource "google_organization_iam_binding" "good_example" {
  org_id  = "org-123"
  role    = "roles/nothingInParticular"
}
