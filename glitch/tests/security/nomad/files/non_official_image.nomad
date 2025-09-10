job "example" {

    group "example" {
        count = 2
        
        network {
            mode = "bridge"
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
                image = "some_random_namespace/nginx:1.29.1-alpine3.22-perl@sha256:9322c38c12e68706f47d42b53622e1c52a351bd963574f4a157b3048d21772e5"

                ports = [ "http" ]
                logging {
                    driver = "elastic/elastic-logging-plugin"
                }
            }
        }
    }
}
