from tests.security.security_helper import BaseSecurityTest
from glitch.tech import Tech

class TestSecurity(BaseSecurityTest):
    TECH = Tech.terraform

    # testing previous implemented code smells
    def test_terraform_http(self) -> None:
        self._help_test(
            "tests/security/terraform/files/http.tf", "script", 1, ["sec_https"], [2]
        )

    def test_terraform_susp_comment(self) -> None:
        self._help_test(
            "tests/security/terraform/files/susp.tf", "script", 1, ["sec_susp_comm"], [8]
        )

    def test_terraform_def_admin(self) -> None:
        self._help_test(
            "tests/security/terraform/files/admin.tf", "script",
            2,
            ["sec_def_admin", "sec_hard_user"],
            [2, 2],
        )

    def test_terraform_empt_pass(self) -> None:
        self._help_test(
            "tests/security/terraform/files/empty.tf", "script", 1, ["sec_empty_pass"], [5]
        )

    def test_terraform_weak_crypt(self) -> None:
        self._help_test(
            "tests/security/terraform/files/weak_crypt.tf", "script", 1, ["sec_weak_crypt"], [4]
        )

    def test_terraform_hard_secr(self) -> None:
        self._help_test(
            "tests/security/terraform/files/hard_secr.tf", "script",
            1,
            ["sec_hard_pass"],
            [5],
        )

    def test_terraform_invalid_bind(self) -> None:
        self._help_test(
            "tests/security/terraform/files/inv_bind.tf", "script", 1, ["sec_invalid_bind"], [19]
        )

    # testing new implemented code smells, or previous ones with new rules for Terraform

    def test_terraform_insecure_access_control(self) -> None:
        self._help_test(
            "tests/security/terraform/files/insecure-access-control/access-to-bigquery-dataset.tf",
            "script",
            1,
            ["sec_access_control"],
            [3],
        )
        self._help_test(
            "tests/security/terraform/files/insecure-access-control/aks-ip-ranges-enabled.tf",
            "script",
            1,
            ["sec_access_control"],
            [1],
        )
        self._help_test(
            "tests/security/terraform/files/insecure-access-control/associated-access-block-to-s3-bucket.tf",
            "script",
            1,
            ["sec_access_control"],
            [1],
        )
        self._help_test(
            "tests/security/terraform/files/insecure-access-control/aws-database-instance-publicly-accessible.tf",
            "script",
            2,
            ["sec_access_control", "sec_access_control"],
            [2, 18],
        )
        self._help_test(
            "tests/security/terraform/files/insecure-access-control/aws-sqs-no-wildcards-in-policy.tf",
            "script",
            1,
            ["sec_access_control"],
            [4],
        )
        self._help_test(
            "tests/security/terraform/files/insecure-access-control/azure-authorization-wildcard-action.tf",
            "script",
            1,
            ["sec_access_control"],
            [7],
        )
        self._help_test(
            "tests/security/terraform/files/insecure-access-control/azure-container-use-rbac-permissions.tf",
            "script",
            1,
            ["sec_access_control"],
            [2],
        )
        self._help_test(
            "tests/security/terraform/files/insecure-access-control/azure-database-not-publicly-accessible.tf",
            "script",
            2,
            ["sec_access_control", "sec_access_control"],
            [1, 6],
        )
        self._help_test(
            "tests/security/terraform/files/insecure-access-control/bucket-public-read-acl.tf",
            "script",
            3,
            ["sec_access_control", "sec_access_control", "sec_access_control"],
            [1, 8, 25],
        )
        self._help_test(
            "tests/security/terraform/files/insecure-access-control/cidr-range-public-access-eks-cluster.tf",
            "script",
            1,
            ["sec_access_control"],
            [1],
        )
        self._help_test(
            "tests/security/terraform/files/insecure-access-control/cross-db-ownership-chaining.tf",
            "script",
            3,
            ["sec_access_control", "sec_access_control", "sec_access_control"],
            [1, 50, 97],
        )
        self._help_test(
            "tests/security/terraform/files/insecure-access-control/data-factory-public-access.tf",
            "script",
            2,
            ["sec_access_control", "sec_access_control"],
            [1, 5],
        )
        self._help_test(
            "tests/security/terraform/files/insecure-access-control/google-compute-no-default-service-account.tf",
            "script",
            2,
            ["sec_access_control", "sec_access_control"],
            [1, 19],
        )
        self._help_test(
            "tests/security/terraform/files/insecure-access-control/google-gke-use-rbac-permissions.tf",
            "script",
            1,
            ["sec_access_control"],
            [17],
        )
        self._help_test(
            "tests/security/terraform/files/insecure-access-control/google-storage-enable-ubla.tf",
            "script",
            2,
            ["sec_access_control", "sec_access_control"],
            [1, 8],
        )
        self._help_test(
            "tests/security/terraform/files/insecure-access-control/google-storage-no-public-access.tf",
            "script",
            3,
            ["sec_access_control", "sec_access_control", "sec_access_control"],
            [4, 10, 22],
        )
        self._help_test(
            "tests/security/terraform/files/insecure-access-control/mq-broker-publicly-exposed.tf",
            "script",
            1,
            ["sec_access_control"],
            [2],
        )
        self._help_test(
            "tests/security/terraform/files/insecure-access-control/prevent-client-disable-encryption.tf",
            "script",
            1,
            ["sec_access_control"],
            [13],
        )
        self._help_test(
            "tests/security/terraform/files/insecure-access-control/private-cluster-nodes.tf",
            "script",
            2,
            ["sec_access_control", "sec_access_control"],
            [1, 19],
        )
        self._help_test(
            "tests/security/terraform/files/insecure-access-control/public-access-eks-cluster.tf",
            "script",
            1,
            ["sec_access_control"],
            [10],
        )
        self._help_test(
            "tests/security/terraform/files/insecure-access-control/public-access-policy.tf",
            "script",
            1,
            ["sec_access_control"],
            [4],
        )
        self._help_test(
            "tests/security/terraform/files/insecure-access-control/public-github-repo.tf",
            "script",
            3,
            ["sec_access_control", "sec_access_control", "sec_access_control"],
            [1, 6, 18],
        )
        self._help_test(
            "tests/security/terraform/files/insecure-access-control/s3-access-through-acl.tf",
            "script",
            1,
            ["sec_access_control"],
            [7],
        )
        self._help_test(
            "tests/security/terraform/files/insecure-access-control/s3-block-public-acl.tf",
            "script",
            2,
            ["sec_access_control", "sec_access_control"],
            [1, 10],
        )
        self._help_test(
            "tests/security/terraform/files/insecure-access-control/s3-block-public-policy.tf",
            "script",
            2,
            ["sec_access_control", "sec_access_control"],
            [1, 11],
        )
        self._help_test(
            "tests/security/terraform/files/insecure-access-control/s3-ignore-public-acl.tf",
            "script",
            2,
            ["sec_access_control", "sec_access_control"],
            [1, 13],
        )
        self._help_test(
            "tests/security/terraform/files/insecure-access-control/s3-restrict-public-bucket.tf",
            "script",
            2,
            ["sec_access_control", "sec_access_control"],
            [1, 12],
        )
        self._help_test(
            "tests/security/terraform/files/insecure-access-control/specify-source-lambda-permission.tf",
            "script",
            1,
            ["sec_access_control"],
            [1],
        )
        self._help_test(
            "tests/security/terraform/files/insecure-access-control/storage-containers-public-access.tf",
            "script",
            1,
            ["sec_access_control"],
            [26],
        )
        self._help_test(
            "tests/security/terraform/files/insecure-access-control/unauthorized-access-api-gateway-methods.tf",
            "script",
            2,
            ["sec_access_control", "sec_access_control"],
            [37, 44],
        )

    def test_terraform_invalid_ip_binding(self) -> None:
        self._help_test(
            "tests/security/terraform/files/invalid-ip-binding/aws-ec2-vpc-no-public-egress-sgr.tf",
            "script",
            2,
            ["sec_invalid_bind", "sec_invalid_bind"],
            [5, 20],
        )
        self._help_test(
            "tests/security/terraform/files/invalid-ip-binding/aws-ec2-vpc-no-public-ingress-acl.tf",
            "script",
            1,
            ["sec_invalid_bind"],
            [7],
        )
        self._help_test(
            "tests/security/terraform/files/invalid-ip-binding/aws-ec2-vpc-no-public-ingress-sgr.tf",
            "script",
            2,
            ["sec_invalid_bind", "sec_invalid_bind"],
            [4, 17],
        )
        self._help_test(
            "tests/security/terraform/files/invalid-ip-binding/azure-network-no-public-egress.tf",
            "script",
            1,
            ["sec_invalid_bind"],
            [3],
        )
        self._help_test(
            "tests/security/terraform/files/invalid-ip-binding/azure-network-no-public-ingress.tf",
            "script",
            1,
            ["sec_invalid_bind"],
            [3],
        )
        self._help_test(
            "tests/security/terraform/files/invalid-ip-binding/cloud-sql-database-publicly-exposed.tf",
            "script",
            1,
            ["sec_invalid_bind"],
            [14],
        )
        self._help_test(
            "tests/security/terraform/files/invalid-ip-binding/compute-firewall-inbound-rule-public-ip.tf",
            "script",
            1,
            ["sec_invalid_bind"],
            [9],
        )
        self._help_test(
            "tests/security/terraform/files/invalid-ip-binding/compute-firewall-outbound-rule-public-ip.tf",
            "script",
            1,
            ["sec_invalid_bind"],
            [9],
        )
        self._help_test(
            "tests/security/terraform/files/invalid-ip-binding/eks-cluster-open-cidr-range.tf",
            "script",
            1,
            ["sec_invalid_bind"],
            [11],
        )
        self._help_test(
            "tests/security/terraform/files/invalid-ip-binding/gke-control-plane-publicly-accessible.tf",
            "script",
            1,
            ["sec_invalid_bind"],
            [8],
        )
        self._help_test(
            "tests/security/terraform/files/invalid-ip-binding/openstack-networking-no-public-egress.tf",
            "script",
            1,
            ["sec_invalid_bind"],
            [8],
        )
        self._help_test(
            "tests/security/terraform/files/invalid-ip-binding/openstack-networking-no-public-ingress.tf",
            "script",
            1,
            ["sec_invalid_bind"],
            [8],
        )
        self._help_test(
            "tests/security/terraform/files/invalid-ip-binding/public-egress-network-policy.tf",
            "script",
            1,
            ["sec_invalid_bind"],
            [27],
        )
        self._help_test(
            "tests/security/terraform/files/invalid-ip-binding/public-ingress-network-policy.tf",
            "script",
            1,
            ["sec_invalid_bind"],
            [27],
        )

    def test_terraform_disabled_authentication(self) -> None:
        self._help_test(
            "tests/security/terraform/files/disabled-authentication/azure-app-service-authentication-activated.tf",
            "script",
            2,
            ["sec_authentication", "sec_authentication"],
            [1, 11],
        )
        self._help_test(
            "tests/security/terraform/files/disabled-authentication/contained-database-disabled.tf",
            "script",
            1,
            ["sec_authentication"],
            [1],
        )
        self._help_test(
            "tests/security/terraform/files/disabled-authentication/disable-password-authentication.tf",
            "script",
            3,
            ["sec_authentication", "sec_authentication", "sec_authentication"],
            [2, 13, 18],
        )
        self._help_test(
            "tests/security/terraform/files/disabled-authentication/gke-basic-auth.tf",
            "script",
            1,
            ["sec_authentication"],
            [4],
        )
        self._help_test(
            "tests/security/terraform/files/disabled-authentication/iam-group-with-mfa.tf",
            "script",
            2,
            ["sec_authentication", "sec_authentication"],
            [7, 53],
        )

    def test_terraform_missing_encryption(self) -> None:
        self._help_test(
            "tests/security/terraform/files/missing-encryption/athena-enable-at-rest-encryption.tf",
            "script",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 10],
        )
        self._help_test(
            "tests/security/terraform/files/missing-encryption/aws-codebuild-enable-encryption.tf",
            "script",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [3, 9],
        )
        self._help_test(
            "tests/security/terraform/files/missing-encryption/aws-ecr-encrypted.tf",
            "script",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 17],
        )
        self._help_test(
            "tests/security/terraform/files/missing-encryption/aws-neptune-at-rest-encryption.tf",
            "script",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 9],
        )
        self._help_test(
            "tests/security/terraform/files/missing-encryption/documentdb-storage-encryption.tf",
            "script",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 9],
        )
        self._help_test(
            "tests/security/terraform/files/missing-encryption/dynamodb-rest-encryption.tf",
            "script",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 9],
        )
        self._help_test(
            "tests/security/terraform/files/missing-encryption/ecs-task-definitions-in-transit-encryption.tf",
            "script",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 29],
        )
        self._help_test(
            "tests/security/terraform/files/missing-encryption/efs-encryption.tf",
            "script",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 6],
        )
        self._help_test(
            "tests/security/terraform/files/missing-encryption/eks-encryption-secrets-enabled.tf",
            "script",
            5,
            [
                "sec_missing_encryption",
                "sec_missing_encryption",
                "sec_missing_encryption",
                "sec_missing_encryption",
                "sec_missing_encryption",
            ],
            [1, 1, 9, 23, 34],
        )
        self._help_test(
            "tests/security/terraform/files/missing-encryption/elasticache-enable-at-rest-encryption.tf",
            "script",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 6],
        )
        self._help_test(
            "tests/security/terraform/files/missing-encryption/elasticache-enable-in-transit-encryption.tf",
            "script",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 7],
        )
        self._help_test(
            "tests/security/terraform/files/missing-encryption/elasticsearch-domain-encrypted.tf",
            "script",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 17],
        )
        self._help_test(
            "tests/security/terraform/files/missing-encryption/elasticsearch-in-transit-encryption.tf",
            "script",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 16],
        )
        self._help_test(
            "tests/security/terraform/files/missing-encryption/emr-enable-at-rest-encryption.tf",
            "script",
            1,
            ["sec_missing_encryption"],
            [4],
        )
        self._help_test(
            "tests/security/terraform/files/missing-encryption/emr-enable-in-transit-encryption.tf",
            "script",
            1,
            ["sec_missing_encryption"],
            [4],
        )
        self._help_test(
            "tests/security/terraform/files/missing-encryption/emr-enable-local-disk-encryption.tf",
            "script",
            1,
            ["sec_missing_encryption"],
            [4],
        )
        self._help_test(
            "tests/security/terraform/files/missing-encryption/emr-s3encryption-mode-sse-kms.tf",
            "script",
            1,
            ["sec_missing_encryption"],
            [4],
        )
        self._help_test(
            "tests/security/terraform/files/missing-encryption/enable-cache-encryption.tf",
            "script",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 6],
        )
        self._help_test(
            "tests/security/terraform/files/missing-encryption/encrypted-ebs-volume.tf",
            "script",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 7],
        )
        self._help_test(
            "tests/security/terraform/files/missing-encryption/encrypted-root-block-device.tf",
            "script",
            4,
            [
                "sec_missing_encryption",
                "sec_missing_encryption",
                "sec_missing_encryption",
                "sec_missing_encryption",
            ],
            [1, 13, 23, 27],
        )
        self._help_test(
            "tests/security/terraform/files/missing-encryption/instance-encrypted-block-device.tf",
            "script",
            1,
            ["sec_missing_encryption"],
            [14],
        )
        self._help_test(
            "tests/security/terraform/files/missing-encryption/kinesis-stream-encryption.tf",
            "script",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 6],
        )
        self._help_test(
            "tests/security/terraform/files/missing-encryption/msk-enable-in-transit-encryption.tf",
            "script",
            3,
            [
                "sec_missing_encryption",
                "sec_missing_encryption",
                "sec_missing_encryption",
            ],
            [1, 14, 15],
        )
        self._help_test(
            "tests/security/terraform/files/missing-encryption/rds-encrypt-cluster-storage-data.tf",
            "script",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 6],
        )
        self._help_test(
            "tests/security/terraform/files/missing-encryption/rds-encrypt-instance-storage-data.tf",
            "script",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 8],
        )
        self._help_test(
            "tests/security/terraform/files/missing-encryption/redshift-cluster-rest-encryption.tf",
            "script",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 6],
        )
        self._help_test(
            "tests/security/terraform/files/missing-encryption/unencrypted-s3-bucket.tf",
            "script",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [25, 64],
        )
        self._help_test(
            "tests/security/terraform/files/missing-encryption/workspaces-disk-encryption.tf",
            "script",
            6,
            [
                "sec_missing_encryption",
                "sec_missing_encryption",
                "sec_missing_encryption",
                "sec_missing_encryption",
                "sec_missing_encryption",
                "sec_missing_encryption",
            ],
            [1, 1, 4, 8, 13, 14],
        )

    def test_terraform_hard_coded_secrets(self) -> None:
        self._help_test(
            "tests/security/terraform/files/hard-coded-secrets/encryption-key-in-plaintext.tf",
            "script",
            1,
            ["sec_hard_secr"],
            [3],
        )
        self._help_test(
            "tests/security/terraform/files/hard-coded-secrets/plaintext-password.tf",
            "script",
            2,
            ["sec_hard_pass", "sec_hard_secr"],
            [2, 2],
        )
        self._help_test(
            "tests/security/terraform/files/hard-coded-secrets/plaintext-value-github-actions.tf",
            "script",
            1,
            ["sec_hard_secr"],
            [5],
        )
        self._help_test(
            "tests/security/terraform/files/hard-coded-secrets/sensitive-credentials-in-vm-custom-data.tf",
            "script",
            2,
            ["sec_hard_pass", "sec_hard_secr"],
            [3, 3],
        )
        self._help_test(
            "tests/security/terraform/files/hard-coded-secrets/sensitive-data-in-plaintext.tf",
            "script",
            2,
            ["sec_hard_pass", "sec_hard_secr"],
            [8, 8],
        )
        self._help_test(
            "tests/security/terraform/files/hard-coded-secrets/sensitive-data-stored-in-user-data.tf",
            "script",
            4,
            ["sec_hard_pass", "sec_hard_secr", "sec_hard_pass", "sec_hard_secr"],
            [2, 2, 14, 14],
        )
        self._help_test(
            "tests/security/terraform/files/hard-coded-secrets/sensitive-environment-variables.tf",
            "script",
            2,
            ["sec_hard_pass", "sec_hard_secr"],
            [2, 2],
        )
        self._help_test(
            "tests/security/terraform/files/hard-coded-secrets/user-data-contains-sensitive-aws-keys.tf",
            "script",
            1,
            ["sec_hard_secr"],
            [9],
        )

    def test_terraform_public_ip(self) -> None:
        self._help_test(
            "tests/security/terraform/files/public-ip/google-compute-intance-with-public-ip.tf",
            "script",
            1,
            ["sec_public_ip"],
            [4],
        )
        self._help_test(
            "tests/security/terraform/files/public-ip/lauch-configuration-public-ip-addr.tf",
            "script",
            1,
            ["sec_public_ip"],
            [2],
        )
        self._help_test(
            "tests/security/terraform/files/public-ip/oracle-compute-no-public-ip.tf",
            "script",
            1,
            ["sec_public_ip"],
            [3],
        )
        self._help_test(
            "tests/security/terraform/files/public-ip/subnet-public-ip-address.tf",
            "script",
            1,
            ["sec_public_ip"],
            [3],
        )

    def test_terraform_use_of_http_without_tls(self) -> None:
        self._help_test(
            "tests/security/terraform/files/use-of-http-without-tls/azure-appservice-enforce-https.tf",
            "script",
            2,
            ["sec_https", "sec_https"],
            [1, 8],
        )
        self._help_test(
            "tests/security/terraform/files/use-of-http-without-tls/azure-storage-enforce-https.tf",
            "script",
            1,
            ["sec_https"],
            [2],
        )
        self._help_test(
            "tests/security/terraform/files/use-of-http-without-tls/cloudfront-enforce-https.tf",
            "script",
            2,
            ["sec_https", "sec_https"],
            [1, 13],
        )
        self._help_test(
            "tests/security/terraform/files/use-of-http-without-tls/digitalocean-compute-enforce-https.tf",
            "script",
            1,
            ["sec_https"],
            [7],
        )
        self._help_test(
            "tests/security/terraform/files/use-of-http-without-tls/elastic-search-enforce-https.tf",
            "script",
            2,
            ["sec_https", "sec_https"],
            [1, 19],
        )
        self._help_test(
            "tests/security/terraform/files/use-of-http-without-tls/elb-use-plain-http.tf",
            "script",
            2,
            ["sec_https", "sec_https"],
            [1, 6],
        )
        self._help_test(
            "tests/security/terraform/files/use-of-http-without-tls/aws-ssm-avoid-leaks-via-http.tf",
            "script",
            1,
            ["sec_https"],
            [8],
        )

    def test_terraform_ssl_tls_mtls_policy(self) -> None:
        self._help_test(
            "tests/security/terraform/files/ssl-tls-mtls-policy/api-gateway-secure-tls-policy.tf",
            "script",
            2,
            ["sec_ssl_tls_policy", "sec_ssl_tls_policy"],
            [1, 5],
        )
        self._help_test(
            "tests/security/terraform/files/ssl-tls-mtls-policy/azure-appservice-require-client-cert.tf",
            "script",
            2,
            ["sec_ssl_tls_policy", "sec_ssl_tls_policy"],
            [1, 9],
        )
        self._help_test(
            "tests/security/terraform/files/ssl-tls-mtls-policy/azure-appservice-secure-tls-policy.tf",
            "script",
            1,
            ["sec_ssl_tls_policy"],
            [3],
        )
        self._help_test(
            "tests/security/terraform/files/ssl-tls-mtls-policy/azure-storage-use-secure-tls-policy.tf",
            "script",
            1,
            ["sec_ssl_tls_policy"],
            [2],
        )
        self._help_test(
            "tests/security/terraform/files/ssl-tls-mtls-policy/cloudfront-secure-tls-policy.tf",
            "script",
            2,
            ["sec_ssl_tls_policy", "sec_ssl_tls_policy"],
            [1, 13],
        )
        self._help_test(
            "tests/security/terraform/files/ssl-tls-mtls-policy/database-enable.ssl-eforcement.tf",
            "script",
            2,
            ["sec_ssl_tls_policy", "sec_ssl_tls_policy"],
            [1, 8],
        )
        self._help_test(
            "tests/security/terraform/files/ssl-tls-mtls-policy/database-secure-tls-policy.tf",
            "script",
            2,
            ["sec_ssl_tls_policy", "sec_ssl_tls_policy"],
            [2, 22],
        )
        self._help_test(
            "tests/security/terraform/files/ssl-tls-mtls-policy/elastic-search-secure-tls-policy.tf",
            "script",
            2,
            ["sec_ssl_tls_policy", "sec_ssl_tls_policy"],
            [1, 20],
        )
        self._help_test(
            "tests/security/terraform/files/ssl-tls-mtls-policy/elb-secure-tls-policy.tf",
            "script",
            2,
            ["sec_ssl_tls_policy", "sec_ssl_tls_policy"],
            [1, 6],
        )
        self._help_test(
            "tests/security/terraform/files/ssl-tls-mtls-policy/google-compute-secure-tls-policy.tf",
            "script",
            2,
            ["sec_ssl_tls_policy", "sec_ssl_tls_policy"],
            [1, 5],
        )
        self._help_test(
            "tests/security/terraform/files/ssl-tls-mtls-policy/sql-encrypt-in-transit-data.tf",
            "script",
            2,
            ["sec_ssl_tls_policy", "sec_ssl_tls_policy"],
            [1, 45],
        )

    def test_terraform_use_of_dns_without_dnssec(self) -> None:
        self._help_test(
            "tests/security/terraform/files/use-of-dns-without-dnssec/cloud-dns-without-dnssec.tf",
            "script",
            2,
            ["sec_dnssec", "sec_dnssec"],
            [1, 6],
        )

    def test_terraform_firewall_misconfiguration(self) -> None:
        self._help_test(
            "tests/security/terraform/files/firewall-misconfiguration/alb-drop-invalid-headers.tf",
            "script",
            2,
            ["sec_firewall_misconfig", "sec_firewall_misconfig"],
            [1, 7],
        )
        self._help_test(
            "tests/security/terraform/files/firewall-misconfiguration/alb-exposed-to-internet.tf",
            "script",
            2,
            ["sec_firewall_misconfig", "sec_firewall_misconfig"],
            [1, 7],
        )
        self._help_test(
            "tests/security/terraform/files/firewall-misconfiguration/azure-keyvault-specify-network-acl.tf",
            "script",
            3,
            [
                "sec_firewall_misconfig",
                "sec_firewall_misconfig",
                "sec_firewall_misconfig",
            ],
            [1, 1, 13],
        )
        self._help_test(
            "tests/security/terraform/files/firewall-misconfiguration/cloudfront-use-waf.tf",
            "script",
            2,
            ["sec_firewall_misconfig", "sec_firewall_misconfig"],
            [1, 14],
        )
        self._help_test(
            "tests/security/terraform/files/firewall-misconfiguration/config-master-authorized-networks.tf",
            "script",
            1,
            ["sec_firewall_misconfig"],
            [1],
        )
        self._help_test(
            "tests/security/terraform/files/firewall-misconfiguration/google-compute-inbound-rule-traffic.tf",
            "script",
            1,
            ["sec_firewall_misconfig"],
            [1],
        )
        self._help_test(
            "tests/security/terraform/files/firewall-misconfiguration/google-compute-no-ip-forward.tf",
            "script",
            1,
            ["sec_firewall_misconfig"],
            [2],
        )
        self._help_test(
            "tests/security/terraform/files/firewall-misconfiguration/google-compute-outbound-rule-traffic.tf",
            "script",
            1,
            ["sec_firewall_misconfig"],
            [1],
        )
        self._help_test(
            "tests/security/terraform/files/firewall-misconfiguration/openstack-compute-no-public-access.tf",
            "script",
            3,
            [
                "sec_firewall_misconfig",
                "sec_firewall_misconfig",
                "sec_firewall_misconfig",
            ],
            [1, 1, 10],
        )

    def test_terraform_missing_threats_detection_and_alerts(self) -> None:
        self._help_test(
            "tests/security/terraform/files/missing-threats-detection-and-alerts/azure-database-disabled-alerts.tf",
            "script",
            1,
            ["sec_threats_detection_alerts"],
            [2],
        )
        self._help_test(
            "tests/security/terraform/files/missing-threats-detection-and-alerts/azure-database-email-admin.tf",
            "script",
            2,
            ["sec_threats_detection_alerts", "sec_threats_detection_alerts"],
            [1, 7],
        )
        self._help_test(
            "tests/security/terraform/files/missing-threats-detection-and-alerts/azure-database-email-for-alerts.tf",
            "script",
            1,
            ["sec_threats_detection_alerts"],
            [1],
        )
        self._help_test(
            "tests/security/terraform/files/missing-threats-detection-and-alerts/azure-security-center-alert-notifications.tf",
            "script",
            2,
            ["sec_threats_detection_alerts", "sec_threats_detection_alerts"],
            [5, 6],
        )
        self._help_test(
            "tests/security/terraform/files/missing-threats-detection-and-alerts/azure-security-require-contact-phone.tf",
            "script",
            2,
            ["sec_threats_detection_alerts", "sec_threats_detection_alerts"],
            [1, 10],
        )
        self._help_test(
            "tests/security/terraform/files/missing-threats-detection-and-alerts/github-repo-vulnerability-alerts.tf",
            "script",
            2,
            ["sec_threats_detection_alerts", "sec_threats_detection_alerts"],
            [1, 16],
        )
        self._help_test(
            "tests/security/terraform/files/missing-threats-detection-and-alerts/aws-ecr-enable-image-scans.tf",
            "script",
            2,
            ["sec_threats_detection_alerts", "sec_threats_detection_alerts"],
            [1, 19],
        )

    def test_terraform_weak_password_key_policy(self) -> None:
        self._help_test(
            "tests/security/terraform/files/weak-password-key-policy/aws-iam-no-password-reuse.tf",
            "script",
            2,
            ["sec_weak_password_key_policy", "sec_weak_password_key_policy"],
            [1, 11],
        )
        self._help_test(
            "tests/security/terraform/files/weak-password-key-policy/aws-iam-require-lowercase-in-passwords.tf",
            "script",
            2,
            ["sec_weak_password_key_policy", "sec_weak_password_key_policy"],
            [1, 11],
        )
        self._help_test(
            "tests/security/terraform/files/weak-password-key-policy/aws-iam-require-numbers-in-passwords.tf",
            "script",
            2,
            ["sec_weak_password_key_policy", "sec_weak_password_key_policy"],
            [1, 11],
        )
        self._help_test(
            "tests/security/terraform/files/weak-password-key-policy/aws-iam-require-symbols-in-passwords.tf",
            "script",
            2,
            ["sec_weak_password_key_policy", "sec_weak_password_key_policy"],
            [1, 11],
        )
        self._help_test(
            "tests/security/terraform/files/weak-password-key-policy/aws-iam-require-uppercase-in-passwords.tf",
            "script",
            2,
            ["sec_weak_password_key_policy", "sec_weak_password_key_policy"],
            [1, 11],
        )
        self._help_test(
            "tests/security/terraform/files/weak-password-key-policy/aws-iam-set-max-password-age.tf",
            "script",
            2,
            ["sec_weak_password_key_policy", "sec_weak_password_key_policy"],
            [1, 11],
        )
        self._help_test(
            "tests/security/terraform/files/weak-password-key-policy/aws-iam-set-minimum-password-length.tf",
            "script",
            2,
            ["sec_weak_password_key_policy", "sec_weak_password_key_policy"],
            [1, 11],
        )
        self._help_test(
            "tests/security/terraform/files/weak-password-key-policy/azure-keyvault-ensure-secret-expiry.tf",
            "script",
            2,
            ["sec_weak_password_key_policy", "sec_weak_password_key_policy"],
            [1, 11],
        )
        self._help_test(
            "tests/security/terraform/files/weak-password-key-policy/azure-keyvault-no-purge.tf",
            "script",
            2,
            ["sec_weak_password_key_policy", "sec_weak_password_key_policy"],
            [1, 11],
        )
        self._help_test(
            "tests/security/terraform/files/weak-password-key-policy/azure-keyvault-ensure-key-expiration-date.tf",
            "script",
            2,
            ["sec_weak_password_key_policy", "sec_weak_password_key_policy"],
            [1, 5],
        )

    def test_terraform_integrity_policy(self) -> None:
        self._help_test(
            "tests/security/terraform/files/integrity-policy/aws-ecr-immutable-repo.tf",
            "script",
            2,
            ["sec_integrity_policy", "sec_integrity_policy"],
            [1, 13],
        )
        self._help_test(
            "tests/security/terraform/files/integrity-policy/google-compute-enable-integrity-monitoring.tf",
            "script",
            1,
            ["sec_integrity_policy"],
            [3],
        )
        self._help_test(
            "tests/security/terraform/files/integrity-policy/google-compute-enable-virtual-tpm.tf",
            "script",
            1,
            ["sec_integrity_policy"],
            [3],
        )

    def test_terraform_sensitive_action_by_iam(self) -> None:
        self._help_test(
            "tests/security/terraform/files/sensitive-action-by-iam/aws-iam-no-policy-wildcards.tf",
            "script",
            3,
            [
                "sec_sensitive_iam_action",
                "sec_sensitive_iam_action",
                "sec_sensitive_iam_action",
            ],
            [7, 8, 20],
        )

    def test_terraform_key_management(self) -> None:
        self._help_test(
            "tests/security/terraform/files/key-management/aws-cloudtrail-encryption-use-cmk.tf",
            "script",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 8],
        )
        self._help_test(
            "tests/security/terraform/files/key-management/aws-cloudwatch-log-group-customer-key.tf",
            "script",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 6],
        )
        self._help_test(
            "tests/security/terraform/files/key-management/aws-documentdb-use-cmk.tf",
            "script",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 7],
        )
        self._help_test(
            "tests/security/terraform/files/key-management/aws-dynamodb-table-use-cmk.tf",
            "script",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 10],
        )
        self._help_test(
            "tests/security/terraform/files/key-management/aws-ebs-use-cmk.tf",
            "script",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 7],
        )
        self._help_test(
            "tests/security/terraform/files/key-management/aws-ecr-use-cmk.tf",
            "script",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 18],
        )
        self._help_test(
            "tests/security/terraform/files/key-management/aws-kinesis-stream-use-cmk.tf",
            "script",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 7],
        )
        self._help_test(
            "tests/security/terraform/files/key-management/aws-kms-auto-rotate-keys.tf",
            "script",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 5],
        )
        self._help_test(
            "tests/security/terraform/files/key-management/aws-neptune-use-cmk.tf",
            "script",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 9],
        )
        self._help_test(
            "tests/security/terraform/files/key-management/aws-sns-topic-encryption-use-cmk.tf",
            "script",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 5],
        )
        self._help_test(
            "tests/security/terraform/files/key-management/aws-sqs-queue-encryption-use-cmk.tf",
            "script",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 5],
        )
        self._help_test(
            "tests/security/terraform/files/key-management/aws-ssm-secret-use-cmk.tf",
            "script",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 7],
        )
        self._help_test(
            "tests/security/terraform/files/key-management/azure-storage-account-use-cmk.tf",
            "script",
            1,
            ["sec_key_management"],
            [1],
        )
        self._help_test(
            "tests/security/terraform/files/key-management/google-compute-disk-encryption-use-cmk.tf",
            "script",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 6],
        )
        self._help_test(
            "tests/security/terraform/files/key-management/google-compute-no-project-wide-ssh-keys.tf",
            "script",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 12],
        )
        self._help_test(
            "tests/security/terraform/files/key-management/google-compute-vm-disk-encryption-use-cmk.tf",
            "script",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 12],
        )
        self._help_test(
            "tests/security/terraform/files/key-management/google-kms-rotate-kms-keys.tf",
            "script",
            3,
            ["sec_key_management", "sec_key_management", "sec_key_management"],
            [1, 9, 15],
        )
        self._help_test(
            "tests/security/terraform/files/key-management/rds-cluster-use-cmk.tf",
            "script",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 7],
        )
        self._help_test(
            "tests/security/terraform/files/key-management/rds-instance-use-cmk.tf",
            "script",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 8],
        )
        self._help_test(
            "tests/security/terraform/files/key-management/rds-performance-insights-use-cmk.tf",
            "script",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 9],
        )
        self._help_test(
            "tests/security/terraform/files/key-management/redshift-cluster-use-cmk.tf",
            "script",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 7],
        )
        self._help_test(
            "tests/security/terraform/files/key-management/s3-encryption-customer-key.tf",
            "script",
            2,
            ["sec_key_management", "sec_key_management"],
            [9, 47],
        )
        self._help_test(
            "tests/security/terraform/files/key-management/digitalocean-compute-use-ssh-keys.tf",
            "script",
            1,
            ["sec_key_management"],
            [1],
        )
        self._help_test(
            "tests/security/terraform/files/key-management/google-storage-bucket-encryption-customer-key.tf",
            "script",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 8],
        )

    def test_terraform_network_security_rules(self) -> None:
        self._help_test(
            "tests/security/terraform/files/network-security-rules/aws-vpc-ec2-use-tcp.tf",
            "script",
            1,
            ["sec_network_security_rules"],
            [2],
        )
        self._help_test(
            "tests/security/terraform/files/network-security-rules/azure-container-configured-network-policy.tf",
            "script",
            2,
            ["sec_network_security_rules", "sec_network_security_rules"],
            [1, 15],
        )
        self._help_test(
            "tests/security/terraform/files/network-security-rules/azure-network-disable-rdp-from-internet.tf",
            "script",
            2,
            ["sec_network_security_rules", "sec_network_security_rules"],
            [8, 32],
        )
        self._help_test(
            "tests/security/terraform/files/network-security-rules/azure-network-ssh-blocked-from-internet.tf",
            "script",
            2,
            ["sec_network_security_rules", "sec_network_security_rules"],
            [8, 32],
        )
        self._help_test(
            "tests/security/terraform/files/network-security-rules/azure-storage-default-action-deny.tf",
            "script",
            3,
            [
                "sec_network_security_rules",
                "sec_network_security_rules",
                "sec_network_security_rules",
            ],
            [1, 8, 21],
        )
        self._help_test(
            "tests/security/terraform/files/network-security-rules/azure-synapse-virtual-network-enabled.tf",
            "script",
            2,
            ["sec_network_security_rules", "sec_network_security_rules"],
            [1, 5],
        )
        self._help_test(
            "tests/security/terraform/files/network-security-rules/google-compute-no-serial-port.tf",
            "script",
            1,
            ["sec_network_security_rules"],
            [4],
        )
        self._help_test(
            "tests/security/terraform/files/network-security-rules/google-gke-enable-ip-aliasing.tf",
            "script",
            1,
            ["sec_network_security_rules"],
            [1],
        )
        self._help_test(
            "tests/security/terraform/files/network-security-rules/google-gke-enable-network-policy.tf",
            "script",
            2,
            ["sec_network_security_rules", "sec_network_security_rules"],
            [1, 19],
        )
        self._help_test(
            "tests/security/terraform/files/network-security-rules/google-iam-no-default-network.tf",
            "script",
            2,
            ["sec_network_security_rules", "sec_network_security_rules"],
            [1, 5],
        )

    def test_terraform_permission_of_iam_policies(self) -> None:
        self._help_test(
            "tests/security/terraform/files/permission-of-iam-policies/default-service-account-not-used-at-folder-level.tf",
            "script",
            2,
            ["sec_permission_iam_policies", "sec_permission_iam_policies"],
            [4, 10],
        )
        self._help_test(
            "tests/security/terraform/files/permission-of-iam-policies/default-service-account-not-used-at-organization-level.tf",
            "script",
            2,
            ["sec_permission_iam_policies", "sec_permission_iam_policies"],
            [4, 10],
        )
        self._help_test(
            "tests/security/terraform/files/permission-of-iam-policies/default-service-account-not-used-at-project-level.tf",
            "script",
            2,
            ["sec_permission_iam_policies", "sec_permission_iam_policies"],
            [4, 10],
        )
        self._help_test(
            "tests/security/terraform/files/permission-of-iam-policies/google-iam-no-folder-level-service-account-impersonation.tf",
            "script",
            1,
            ["sec_permission_iam_policies"],
            [3],
        )
        self._help_test(
            "tests/security/terraform/files/permission-of-iam-policies/google-iam-no-organization-level-service-account-impersonation.tf",
            "script",
            1,
            ["sec_permission_iam_policies"],
            [3],
        )
        self._help_test(
            "tests/security/terraform/files/permission-of-iam-policies/google-iam-no-project-level-service-account-impersonation.tf",
            "script",
            1,
            ["sec_permission_iam_policies"],
            [3],
        )
        self._help_test(
            "tests/security/terraform/files/permission-of-iam-policies/google-iam-no-user-granted-permissions.tf",
            "script",
            2,
            ["sec_permission_iam_policies", "sec_permission_iam_policies"],
            [2, 6],
        )
        self._help_test(
            "tests/security/terraform/files/permission-of-iam-policies/iam-policies-attached-only-to-groups-or-roles.tf",
            "script",
            1,
            ["sec_permission_iam_policies"],
            [7],
        )

    def test_terraform_logging(self) -> None:
        self._help_test(
            "tests/security/terraform/files/logging/aws-api-gateway-enable-access-logging.tf",
            "script",
            4,
            ["sec_logging", "sec_logging", "sec_logging", "sec_logging"],
            [1, 4, 10, 17],
        )
        self._help_test(
            "tests/security/terraform/files/logging/aws-api-gateway-enable-tracing.tf",
            "script",
            2,
            ["sec_logging", "sec_logging"],
            [1, 9],
        )
        self._help_test(
            "tests/security/terraform/files/logging/aws-cloudfront-enable-logging.tf",
            "script",
            2,
            ["sec_logging", "sec_logging"],
            [1, 13],
        )
        self._help_test(
            "tests/security/terraform/files/logging/aws-cloudtrail-enable-log-validation.tf",
            "script",
            2,
            ["sec_logging", "sec_logging"],
            [1, 7],
        )
        self._help_test(
            "tests/security/terraform/files/logging/aws-cloudtrail-ensure-cloudwatch-integration.tf",
            "script",
            2,
            ["sec_logging", "sec_logging"],
            [1, 7],
        )
        self._help_test(
            "tests/security/terraform/files/logging/aws-documentdb-enable-log-export.tf",
            "script",
            2,
            ["sec_logging", "sec_logging"],
            [1, 7],
        )
        self._help_test(
            "tests/security/terraform/files/logging/aws-eks-enable-control-plane-logging.tf",
            "script",
            2,
            ["sec_logging", "sec_logging"],
            [1, 15],
        )
        self._help_test(
            "tests/security/terraform/files/logging/aws-elastic-search-enable-domain-logging.tf",
            "script",
            3,
            ["sec_logging", "sec_logging", "sec_logging"],
            [1, 17, 36],
        )
        self._help_test(
            "tests/security/terraform/files/logging/aws-lambda-enable-tracing.tf",
            "script",
            2,
            ["sec_logging", "sec_logging"],
            [1, 6],
        )
        self._help_test(
            "tests/security/terraform/files/logging/aws-mq-enable-audit-logging.tf",
            "script",
            2,
            ["sec_logging", "sec_logging"],
            [1, 10],
        )
        self._help_test(
            "tests/security/terraform/files/logging/aws-mq-enable-general-logging.tf",
            "script",
            2,
            ["sec_logging", "sec_logging"],
            [1, 10],
        )
        self._help_test(
            "tests/security/terraform/files/logging/aws-msk-enable-logging.tf",
            "script",
            5,
            ["sec_logging", "sec_logging", "sec_logging", "sec_logging", "sec_logging"],
            [1, 14, 48, 51, 54],
        )
        self._help_test(
            "tests/security/terraform/files/logging/aws-neptune-enable-log-export.tf",
            "script",
            2,
            ["sec_logging", "sec_logging"],
            [1, 7],
        )
        self._help_test(
            "tests/security/terraform/files/logging/aws-rds-enable-performance-insights.tf",
            "script",
            2,
            ["sec_logging", "sec_logging"],
            [1, 7],
        )
        self._help_test(
            "tests/security/terraform/files/logging/aws-s3-enable-bucket-logging.tf",
            "script",
            1,
            ["sec_logging"],
            [1],
        )
        self._help_test(
            "tests/security/terraform/files/logging/azure-container-aks-logging-configured.tf",
            "script",
            2,
            ["sec_logging", "sec_logging"],
            [1, 13],
        )
        self._help_test(
            "tests/security/terraform/files/logging/azure-monitor-activity-log-retention-set.tf",
            "script",
            2,
            ["sec_logging", "sec_logging"],
            [1, 8],
        )
        self._help_test(
            "tests/security/terraform/files/logging/azure-monitor-capture-all-activities.tf",
            "script",
            2,
            ["sec_logging", "sec_logging"],
            [1, 8],
        )
        self._help_test(
            "tests/security/terraform/files/logging/azure-mssql-database-enable-audit.tf",
            "script",
            1,
            ["sec_logging"],
            [1],
        )
        self._help_test(
            "tests/security/terraform/files/logging/azure-mssql-server-and-database-retention-period-set.tf",
            "script",
            3,
            ["sec_logging", "sec_logging", "sec_logging"],
            [3, 13, 18],
        )
        self._help_test(
            "tests/security/terraform/files/logging/azure-mssql-server-enable-audit.tf",
            "script",
            1,
            ["sec_logging"],
            [1],
        )
        self._help_test(
            "tests/security/terraform/files/logging/azure-network-retention-policy-set.tf",
            "script",
            2,
            ["sec_logging", "sec_logging"],
            [1, 7],
        )
        self._help_test(
            "tests/security/terraform/files/logging/azure-postgres-configuration-enabled-logs.tf",
            "script",
            3,
            ["sec_logging", "sec_logging", "sec_logging"],
            [5, 12, 19],
        )
        self._help_test(
            "tests/security/terraform/files/logging/azure-storage-queue-services-logging-enabled.tf",
            "script",
            6,
            [
                "sec_logging",
                "sec_logging",
                "sec_logging",
                "sec_logging",
                "sec_logging",
                "sec_logging",
            ],
            [1, 1, 1, 15, 16, 17],
        )
        self._help_test(
            "tests/security/terraform/files/logging/ensure-cloudwatch-log-group-specifies-retention-days.tf",
            "script",
            2,
            ["sec_logging", "sec_logging"],
            [1, 6],
        )
        self._help_test(
            "tests/security/terraform/files/logging/google-compute-enable-vpc-flow-logs.tf",
            "script",
            1,
            ["sec_logging"],
            [1],
        )
        self._help_test(
            "tests/security/terraform/files/logging/google-gke-enable-stackdriver-logging.tf",
            "script",
            1,
            ["sec_logging"],
            [2],
        )
        self._help_test(
            "tests/security/terraform/files/logging/google-gke-enable-stackdriver-monitoring.tf",
            "script",
            1,
            ["sec_logging"],
            [2],
        )
        self._help_test(
            "tests/security/terraform/files/logging/google-sql-database-log-flags.tf",
            "script",
            12,
            [
                "sec_logging",
                "sec_logging",
                "sec_logging",
                "sec_logging",
                "sec_logging",
                "sec_logging",
                "sec_logging",
                "sec_logging",
                "sec_logging",
                "sec_logging",
                "sec_logging",
                "sec_logging",
            ],
            [1, 1, 1, 1, 1, 36, 40, 44, 48, 52, 56, 60],
        )
        self._help_test(
            "tests/security/terraform/files/logging/storage-logging-enabled-for-blob-service-for-read-requests.tf",
            "script",
            4,
            ["sec_logging", "sec_logging", "sec_logging", "sec_logging"],
            [1, 8, 49, 79],
        )
        self._help_test(
            "tests/security/terraform/files/logging/aws-ecs-enable-container-insight.tf",
            "script",
            3,
            ["sec_logging", "sec_logging", "sec_logging"],
            [1, 7, 11],
        )
        self._help_test(
            "tests/security/terraform/files/logging/aws-vpc-flow-logs-enabled.tf",
            "script",
            1,
            ["sec_logging"],
            [11],
        )

    def test_terraform_attached_resource(self) -> None:
        self._help_test(
            "tests/security/terraform/files/attached-resource/aws_route53_attached_resource.tf",
            "script",
            2,
            ["sec_attached_resource", "sec_attached_resource"],
            [12, 16],
        )

    def test_terraform_versioning(self) -> None:
        self._help_test(
            "tests/security/terraform/files/versioning/aws-s3-enable-versioning.tf",
            "script",
            2,
            ["sec_versioning", "sec_versioning"],
            [1, 8],
        )
        self._help_test(
            "tests/security/terraform/files/versioning/digitalocean-spaces-versioning-enabled.tf",
            "script",
            2,
            ["sec_versioning", "sec_versioning"],
            [1, 7],
        )

    def test_terraform_naming(self) -> None:
        self._help_test(
            "tests/security/terraform/files/naming/aws-ec2-description-to-security-group-rule.tf",
            "script",
            2,
            ["sec_naming", "sec_naming"],
            [1, 14],
        )
        self._help_test(
            "tests/security/terraform/files/naming/aws-ec2-description-to-security-group.tf",
            "script",
            2,
            ["sec_naming", "sec_naming"],
            [1, 5],
        )
        self._help_test(
            "tests/security/terraform/files/naming/aws-elasticache-description-for-security-group.tf",
            "script",
            2,
            ["sec_naming", "sec_naming"],
            [1, 7],
        )
        self._help_test(
            "tests/security/terraform/files/naming/naming-rules-storage-accounts.tf",
            "script",
            2,
            ["sec_naming", "sec_naming"],
            [2, 21],
        )
        self._help_test(
            "tests/security/terraform/files/naming/openstack-networking-describe-security-group.tf",
            "script",
            2,
            ["sec_naming", "sec_naming"],
            [1, 5],
        )
        self._help_test(
            "tests/security/terraform/files/naming/google-gke-use-cluster-labels.tf",
            "script",
            2,
            ["sec_naming", "sec_naming"],
            [1, 19],
        )

    def test_terraform_replication(self) -> None:
        self._help_test(
            "tests/security/terraform/files/replication/s3-bucket-cross-region-replication.tf",
            "script",
            2,
            ["sec_replication", "sec_replication"],
            [9, 16],
        )
