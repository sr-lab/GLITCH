job "example" {

    group "example" {
        count = 2
        
        network {
            mode = "host"
            port "http" { }
        }

        service {
            name = "server-api"
            port = "http"
            tags = ["http"]

            connect {
                sidecar_service {}
            }
            check {
                name     = "http_probe"
                type     = "http"
                interval = "10s"
                timeout  = "1s"
            }
        }

        task "example-api" {
            driver = "docker"

            config {
                image = "ubuntu:24.04@sha256:9322c38c12e68706f47d42b53622e1c52a351bd963574f4a157b3048d21772e5"

                ports = [ "http" ]
                logging {
                    driver = "elastic/elastic-logging-plugin"
                }
            }

        }
    }
}
