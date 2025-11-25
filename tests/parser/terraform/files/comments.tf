#comment1
//comment2
resource "google_bigquery_dataset" "dataset" {
  /*comment3
  default_table_expiration_ms = 3600000
  
  finish comment3 */ #comment4

  default_table_expiration_ms = 3600000 #comment5

  labels = {
    env = "default" #comment inside dict
    //comment2 inside dict
    test = "value1"
  }
}
