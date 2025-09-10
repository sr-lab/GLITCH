job "example" {

    group "example" {
        count = 2
        
        network {
            mode = "bridge"
            port "http" { }
            port "check" { }
        }

        service {
            name = "server-proxy"
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

        service {
            name = "service-api"
            port = "check"
            tags = ["check"]

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
                image = "nginx:1.29.1-alpine3.22-perl@sha256:9322c38c12e68706f47d42b53622e1c52a351bd963574f4a157b3048d21772e5"

                ports = [ "http" ]
                logging {
                    driver = "elastic/elastic-logging-plugin"
                }
            }
        }

        task "example-service" {
            driver = "docker"

            config {
                image = "someone/exampleapp:v234.12@sha256:9322c38c12e68706f47d42b53622e1c52a351bd963574f4a157b3048d21772e5"
                ports = [ "check" ]
                logging {
                    driver = "elastic/elastic-logging-plugin"
                }
            }
        }

        task "example-service2" {
            driver = "docker"

            config {
                image = "someone/exampleapp2:v234.12@sha256:9322c38c12e68706f47d42b53622e1c52a351bd963574f4a157b3048d21772e5"
                ports = [ "check" ]
                logging {
                    driver = "elastic/elastic-logging-plugin"
                }
            }
        }
    }
}
