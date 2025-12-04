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
                name     = "grpc_probe"
                type     = "http"
                interval = "10s"
                timeout  = "1s"
            }
        }

        task "example-api" {
            driver = "docker"

            config {
                image = "nginx:1.29.1-alpine3.22-perl"

                ports = [ "http" ]
                logging {
                    driver = "elastic/elastic-logging-plugin"
                }
            }
        }
    }
}
