resource "google_organization_iam_member" "bad_example" {
  org_id = "your-org-id"
  role    = "roles/whatever"
  member  = "123-compute@developer.gserviceaccount.comm"
}

resource "google_organization_iam_member" "bad_example2" {
  org_id = "your-org-id"
  role    = "roles/whatever"
  member  = "123@appspot.gserviceaccount.com"
}

resource "google_organization_iam_member" "good_example" {
  org_id = "your-org-id"
  role    = "roles/whatever"
  member  = "123@something.com"
}
