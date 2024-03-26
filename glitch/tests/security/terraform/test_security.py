import unittest

from glitch.analysis.security import SecurityVisitor
from glitch.parsers.terraform import TerraformParser
from glitch.tech import Tech


class TestSecurity(unittest.TestCase):
    def __help_test(self, path, n_errors: int, codes, lines) -> None:
        parser = TerraformParser()
        inter = parser.parse(path, "script", False)
        analysis = SecurityVisitor(Tech.terraform)
        analysis.config("configs/terraform.ini")
        errors = list(
            filter(lambda e: e.code.startswith("sec_"), set(analysis.check(inter)))
        )
        errors = sorted(errors, key=lambda e: (e.path, e.line, e.code))
        self.assertEqual(len(errors), n_errors)
        for i in range(n_errors):
            self.assertEqual(errors[i].code, codes[i])
            self.assertEqual(errors[i].line, lines[i])

    # testing previous implemented code smells
    def test_terraform_http(self) -> None:
        self.__help_test(
            "tests/security/terraform/files/http.tf", 1, ["sec_https"], [2]
        )

    def test_terraform_susp_comment(self) -> None:
        self.__help_test(
            "tests/security/terraform/files/susp.tf", 1, ["sec_susp_comm"], [8]
        )

    def test_terraform_def_admin(self) -> None:
        self.__help_test(
            "tests/security/terraform/files/admin.tf",
            3,
            ["sec_def_admin", "sec_hard_secr", "sec_hard_user"],
            [2, 2, 2],
        )

    def test_terraform_empt_pass(self) -> None:
        self.__help_test(
            "tests/security/terraform/files/empty.tf", 1, ["sec_empty_pass"], [5]
        )

    def test_terraform_weak_crypt(self) -> None:
        self.__help_test(
            "tests/security/terraform/files/weak_crypt.tf", 1, ["sec_weak_crypt"], [4]
        )

    def test_terraform_hard_secr(self) -> None:
        self.__help_test(
            "tests/security/terraform/files/hard_secr.tf",
            2,
            ["sec_hard_pass", "sec_hard_secr"],
            [5, 5],
        )

    def test_terraform_invalid_bind(self) -> None:
        self.__help_test(
            "tests/security/terraform/files/inv_bind.tf", 1, ["sec_invalid_bind"], [19]
        )

    # testing new implemented code smells, or previous ones with new rules for Terraform

    def test_terraform_insecure_access_control(self) -> None:
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/access-to-bigquery-dataset.tf",
            1,
            ["sec_access_control"],
            [3],
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/aks-ip-ranges-enabled.tf",
            1,
            ["sec_access_control"],
            [1],
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/associated-access-block-to-s3-bucket.tf",
            1,
            ["sec_access_control"],
            [1],
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/aws-database-instance-publicly-accessible.tf",
            2,
            ["sec_access_control", "sec_access_control"],
            [2, 18],
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/aws-sqs-no-wildcards-in-policy.tf",
            1,
            ["sec_access_control"],
            [4],
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/azure-authorization-wildcard-action.tf",
            1,
            ["sec_access_control"],
            [7],
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/azure-container-use-rbac-permissions.tf",
            1,
            ["sec_access_control"],
            [2],
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/azure-database-not-publicly-accessible.tf",
            2,
            ["sec_access_control", "sec_access_control"],
            [1, 6],
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/bucket-public-read-acl.tf",
            3,
            ["sec_access_control", "sec_access_control", "sec_access_control"],
            [1, 8, 25],
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/cidr-range-public-access-eks-cluster.tf",
            1,
            ["sec_access_control"],
            [1],
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/cross-db-ownership-chaining.tf",
            3,
            ["sec_access_control", "sec_access_control", "sec_access_control"],
            [1, 50, 97],
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/data-factory-public-access.tf",
            2,
            ["sec_access_control", "sec_access_control"],
            [1, 5],
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/google-compute-no-default-service-account.tf",
            2,
            ["sec_access_control", "sec_access_control"],
            [1, 19],
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/google-gke-use-rbac-permissions.tf",
            1,
            ["sec_access_control"],
            [17],
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/google-storage-enable-ubla.tf",
            2,
            ["sec_access_control", "sec_access_control"],
            [1, 8],
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/google-storage-no-public-access.tf",
            3,
            ["sec_access_control", "sec_access_control", "sec_access_control"],
            [4, 10, 22],
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/mq-broker-publicly-exposed.tf",
            1,
            ["sec_access_control"],
            [2],
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/prevent-client-disable-encryption.tf",
            1,
            ["sec_access_control"],
            [13],
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/private-cluster-nodes.tf",
            2,
            ["sec_access_control", "sec_access_control"],
            [1, 19],
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/public-access-eks-cluster.tf",
            1,
            ["sec_access_control"],
            [10],
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/public-access-policy.tf",
            1,
            ["sec_access_control"],
            [4],
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/public-github-repo.tf",
            3,
            ["sec_access_control", "sec_access_control", "sec_access_control"],
            [1, 6, 18],
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/s3-access-through-acl.tf",
            1,
            ["sec_access_control"],
            [7],
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/s3-block-public-acl.tf",
            2,
            ["sec_access_control", "sec_access_control"],
            [1, 10],
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/s3-block-public-policy.tf",
            2,
            ["sec_access_control", "sec_access_control"],
            [1, 11],
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/s3-ignore-public-acl.tf",
            2,
            ["sec_access_control", "sec_access_control"],
            [1, 13],
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/s3-restrict-public-bucket.tf",
            2,
            ["sec_access_control", "sec_access_control"],
            [1, 12],
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/specify-source-lambda-permission.tf",
            1,
            ["sec_access_control"],
            [1],
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/storage-containers-public-access.tf",
            1,
            ["sec_access_control"],
            [26],
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/unauthorized-access-api-gateway-methods.tf",
            2,
            ["sec_access_control", "sec_access_control"],
            [37, 44],
        )

    def test_terraform_invalid_ip_binding(self) -> None:
        self.__help_test(
            "tests/security/terraform/files/invalid-ip-binding/aws-ec2-vpc-no-public-egress-sgr.tf",
            2,
            ["sec_invalid_bind", "sec_invalid_bind"],
            [5, 20],
        )
        self.__help_test(
            "tests/security/terraform/files/invalid-ip-binding/aws-ec2-vpc-no-public-ingress-acl.tf",
            1,
            ["sec_invalid_bind"],
            [7],
        )
        self.__help_test(
            "tests/security/terraform/files/invalid-ip-binding/aws-ec2-vpc-no-public-ingress-sgr.tf",
            2,
            ["sec_invalid_bind", "sec_invalid_bind"],
            [4, 17],
        )
        self.__help_test(
            "tests/security/terraform/files/invalid-ip-binding/azure-network-no-public-egress.tf",
            1,
            ["sec_invalid_bind"],
            [3],
        )
        self.__help_test(
            "tests/security/terraform/files/invalid-ip-binding/azure-network-no-public-ingress.tf",
            1,
            ["sec_invalid_bind"],
            [3],
        )
        self.__help_test(
            "tests/security/terraform/files/invalid-ip-binding/cloud-sql-database-publicly-exposed.tf",
            1,
            ["sec_invalid_bind"],
            [14],
        )
        self.__help_test(
            "tests/security/terraform/files/invalid-ip-binding/compute-firewall-inbound-rule-public-ip.tf",
            1,
            ["sec_invalid_bind"],
            [9],
        )
        self.__help_test(
            "tests/security/terraform/files/invalid-ip-binding/compute-firewall-outbound-rule-public-ip.tf",
            1,
            ["sec_invalid_bind"],
            [9],
        )
        self.__help_test(
            "tests/security/terraform/files/invalid-ip-binding/eks-cluster-open-cidr-range.tf",
            1,
            ["sec_invalid_bind"],
            [11],
        )
        self.__help_test(
            "tests/security/terraform/files/invalid-ip-binding/gke-control-plane-publicly-accessible.tf",
            1,
            ["sec_invalid_bind"],
            [8],
        )
        self.__help_test(
            "tests/security/terraform/files/invalid-ip-binding/openstack-networking-no-public-egress.tf",
            1,
            ["sec_invalid_bind"],
            [8],
        )
        self.__help_test(
            "tests/security/terraform/files/invalid-ip-binding/openstack-networking-no-public-ingress.tf",
            1,
            ["sec_invalid_bind"],
            [8],
        )
        self.__help_test(
            "tests/security/terraform/files/invalid-ip-binding/public-egress-network-policy.tf",
            1,
            ["sec_invalid_bind"],
            [27],
        )
        self.__help_test(
            "tests/security/terraform/files/invalid-ip-binding/public-ingress-network-policy.tf",
            1,
            ["sec_invalid_bind"],
            [27],
        )

    def test_terraform_disabled_authentication(self) -> None:
        self.__help_test(
            "tests/security/terraform/files/disabled-authentication/azure-app-service-authentication-activated.tf",
            2,
            ["sec_authentication", "sec_authentication"],
            [1, 11],
        )
        self.__help_test(
            "tests/security/terraform/files/disabled-authentication/contained-database-disabled.tf",
            1,
            ["sec_authentication"],
            [1],
        )
        self.__help_test(
            "tests/security/terraform/files/disabled-authentication/disable-password-authentication.tf",
            3,
            ["sec_authentication", "sec_authentication", "sec_authentication"],
            [2, 13, 18],
        )
        self.__help_test(
            "tests/security/terraform/files/disabled-authentication/gke-basic-auth.tf",
            1,
            ["sec_authentication"],
            [4],
        )
        self.__help_test(
            "tests/security/terraform/files/disabled-authentication/iam-group-with-mfa.tf",
            2,
            ["sec_authentication", "sec_authentication"],
            [7, 53],
        )

    def test_terraform_missing_encryption(self) -> None:
        self.__help_test(
            "tests/security/terraform/files/missing-encryption/athena-enable-at-rest-encryption.tf",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 10],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-encryption/aws-codebuild-enable-encryption.tf",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [3, 9],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-encryption/aws-ecr-encrypted.tf",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 17],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-encryption/aws-neptune-at-rest-encryption.tf",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 9],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-encryption/documentdb-storage-encryption.tf",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 9],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-encryption/dynamodb-rest-encryption.tf",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 9],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-encryption/ecs-task-definitions-in-transit-encryption.tf",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 29],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-encryption/efs-encryption.tf",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 6],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-encryption/eks-encryption-secrets-enabled.tf",
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
        self.__help_test(
            "tests/security/terraform/files/missing-encryption/elasticache-enable-at-rest-encryption.tf",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 6],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-encryption/elasticache-enable-in-transit-encryption.tf",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 7],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-encryption/elasticsearch-domain-encrypted.tf",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 17],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-encryption/elasticsearch-in-transit-encryption.tf",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 16],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-encryption/emr-enable-at-rest-encryption.tf",
            1,
            ["sec_missing_encryption"],
            [4],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-encryption/emr-enable-in-transit-encryption.tf",
            1,
            ["sec_missing_encryption"],
            [4],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-encryption/emr-enable-local-disk-encryption.tf",
            1,
            ["sec_missing_encryption"],
            [4],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-encryption/emr-s3encryption-mode-sse-kms.tf",
            1,
            ["sec_missing_encryption"],
            [4],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-encryption/enable-cache-encryption.tf",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 6],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-encryption/encrypted-ebs-volume.tf",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 7],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-encryption/encrypted-root-block-device.tf",
            4,
            [
                "sec_missing_encryption",
                "sec_missing_encryption",
                "sec_missing_encryption",
                "sec_missing_encryption",
            ],
            [1, 13, 23, 27],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-encryption/instance-encrypted-block-device.tf",
            1,
            ["sec_missing_encryption"],
            [14],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-encryption/kinesis-stream-encryption.tf",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 6],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-encryption/msk-enable-in-transit-encryption.tf",
            3,
            [
                "sec_missing_encryption",
                "sec_missing_encryption",
                "sec_missing_encryption",
            ],
            [1, 14, 15],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-encryption/rds-encrypt-cluster-storage-data.tf",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 6],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-encryption/rds-encrypt-instance-storage-data.tf",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 8],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-encryption/redshift-cluster-rest-encryption.tf",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [1, 6],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-encryption/unencrypted-s3-bucket.tf",
            2,
            ["sec_missing_encryption", "sec_missing_encryption"],
            [25, 64],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-encryption/workspaces-disk-encryption.tf",
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
        self.__help_test(
            "tests/security/terraform/files/hard-coded-secrets/encryption-key-in-plaintext.tf",
            1,
            ["sec_hard_secr"],
            [3],
        )
        self.__help_test(
            "tests/security/terraform/files/hard-coded-secrets/plaintext-password.tf",
            2,
            ["sec_hard_pass", "sec_hard_secr"],
            [2, 2],
        )
        self.__help_test(
            "tests/security/terraform/files/hard-coded-secrets/plaintext-value-github-actions.tf",
            1,
            ["sec_hard_secr"],
            [5],
        )
        self.__help_test(
            "tests/security/terraform/files/hard-coded-secrets/sensitive-credentials-in-vm-custom-data.tf",
            2,
            ["sec_hard_pass", "sec_hard_secr"],
            [3, 3],
        )
        self.__help_test(
            "tests/security/terraform/files/hard-coded-secrets/sensitive-data-in-plaintext.tf",
            2,
            ["sec_hard_pass", "sec_hard_secr"],
            [8, 8],
        )
        self.__help_test(
            "tests/security/terraform/files/hard-coded-secrets/sensitive-data-stored-in-user-data.tf",
            4,
            ["sec_hard_pass", "sec_hard_secr", "sec_hard_pass", "sec_hard_secr"],
            [2, 2, 14, 14],
        )
        self.__help_test(
            "tests/security/terraform/files/hard-coded-secrets/sensitive-environment-variables.tf",
            2,
            ["sec_hard_pass", "sec_hard_secr"],
            [2, 2],
        )
        self.__help_test(
            "tests/security/terraform/files/hard-coded-secrets/user-data-contains-sensitive-aws-keys.tf",
            1,
            ["sec_hard_secr"],
            [9],
        )

    def test_terraform_public_ip(self) -> None:
        self.__help_test(
            "tests/security/terraform/files/public-ip/google-compute-intance-with-public-ip.tf",
            1,
            ["sec_public_ip"],
            [4],
        )
        self.__help_test(
            "tests/security/terraform/files/public-ip/lauch-configuration-public-ip-addr.tf",
            1,
            ["sec_public_ip"],
            [2],
        )
        self.__help_test(
            "tests/security/terraform/files/public-ip/oracle-compute-no-public-ip.tf",
            1,
            ["sec_public_ip"],
            [3],
        )
        self.__help_test(
            "tests/security/terraform/files/public-ip/subnet-public-ip-address.tf",
            1,
            ["sec_public_ip"],
            [3],
        )

    def test_terraform_use_of_http_without_tls(self) -> None:
        self.__help_test(
            "tests/security/terraform/files/use-of-http-without-tls/azure-appservice-enforce-https.tf",
            2,
            ["sec_https", "sec_https"],
            [1, 8],
        )
        self.__help_test(
            "tests/security/terraform/files/use-of-http-without-tls/azure-storage-enforce-https.tf",
            1,
            ["sec_https"],
            [2],
        )
        self.__help_test(
            "tests/security/terraform/files/use-of-http-without-tls/cloudfront-enforce-https.tf",
            2,
            ["sec_https", "sec_https"],
            [1, 13],
        )
        self.__help_test(
            "tests/security/terraform/files/use-of-http-without-tls/digitalocean-compute-enforce-https.tf",
            1,
            ["sec_https"],
            [7],
        )
        self.__help_test(
            "tests/security/terraform/files/use-of-http-without-tls/elastic-search-enforce-https.tf",
            2,
            ["sec_https", "sec_https"],
            [1, 19],
        )
        self.__help_test(
            "tests/security/terraform/files/use-of-http-without-tls/elb-use-plain-http.tf",
            2,
            ["sec_https", "sec_https"],
            [1, 6],
        )
        self.__help_test(
            "tests/security/terraform/files/use-of-http-without-tls/aws-ssm-avoid-leaks-via-http.tf",
            1,
            ["sec_https"],
            [8],
        )

    def test_terraform_ssl_tls_mtls_policy(self) -> None:
        self.__help_test(
            "tests/security/terraform/files/ssl-tls-mtls-policy/api-gateway-secure-tls-policy.tf",
            2,
            ["sec_ssl_tls_policy", "sec_ssl_tls_policy"],
            [1, 5],
        )
        self.__help_test(
            "tests/security/terraform/files/ssl-tls-mtls-policy/azure-appservice-require-client-cert.tf",
            2,
            ["sec_ssl_tls_policy", "sec_ssl_tls_policy"],
            [1, 9],
        )
        self.__help_test(
            "tests/security/terraform/files/ssl-tls-mtls-policy/azure-appservice-secure-tls-policy.tf",
            1,
            ["sec_ssl_tls_policy"],
            [3],
        )
        self.__help_test(
            "tests/security/terraform/files/ssl-tls-mtls-policy/azure-storage-use-secure-tls-policy.tf",
            1,
            ["sec_ssl_tls_policy"],
            [2],
        )
        self.__help_test(
            "tests/security/terraform/files/ssl-tls-mtls-policy/cloudfront-secure-tls-policy.tf",
            2,
            ["sec_ssl_tls_policy", "sec_ssl_tls_policy"],
            [1, 13],
        )
        self.__help_test(
            "tests/security/terraform/files/ssl-tls-mtls-policy/database-enable.ssl-eforcement.tf",
            2,
            ["sec_ssl_tls_policy", "sec_ssl_tls_policy"],
            [1, 8],
        )
        self.__help_test(
            "tests/security/terraform/files/ssl-tls-mtls-policy/database-secure-tls-policy.tf",
            2,
            ["sec_ssl_tls_policy", "sec_ssl_tls_policy"],
            [2, 22],
        )
        self.__help_test(
            "tests/security/terraform/files/ssl-tls-mtls-policy/elastic-search-secure-tls-policy.tf",
            2,
            ["sec_ssl_tls_policy", "sec_ssl_tls_policy"],
            [1, 20],
        )
        self.__help_test(
            "tests/security/terraform/files/ssl-tls-mtls-policy/elb-secure-tls-policy.tf",
            2,
            ["sec_ssl_tls_policy", "sec_ssl_tls_policy"],
            [1, 6],
        )
        self.__help_test(
            "tests/security/terraform/files/ssl-tls-mtls-policy/google-compute-secure-tls-policy.tf",
            2,
            ["sec_ssl_tls_policy", "sec_ssl_tls_policy"],
            [1, 5],
        )
        self.__help_test(
            "tests/security/terraform/files/ssl-tls-mtls-policy/sql-encrypt-in-transit-data.tf",
            2,
            ["sec_ssl_tls_policy", "sec_ssl_tls_policy"],
            [1, 45],
        )

    def test_terraform_use_of_dns_without_dnssec(self) -> None:
        self.__help_test(
            "tests/security/terraform/files/use-of-dns-without-dnssec/cloud-dns-without-dnssec.tf",
            2,
            ["sec_dnssec", "sec_dnssec"],
            [1, 6],
        )

    def test_terraform_firewall_misconfiguration(self) -> None:
        self.__help_test(
            "tests/security/terraform/files/firewall-misconfiguration/alb-drop-invalid-headers.tf",
            2,
            ["sec_firewall_misconfig", "sec_firewall_misconfig"],
            [1, 7],
        )
        self.__help_test(
            "tests/security/terraform/files/firewall-misconfiguration/alb-exposed-to-internet.tf",
            2,
            ["sec_firewall_misconfig", "sec_firewall_misconfig"],
            [1, 7],
        )
        self.__help_test(
            "tests/security/terraform/files/firewall-misconfiguration/azure-keyvault-specify-network-acl.tf",
            3,
            [
                "sec_firewall_misconfig",
                "sec_firewall_misconfig",
                "sec_firewall_misconfig",
            ],
            [1, 1, 13],
        )
        self.__help_test(
            "tests/security/terraform/files/firewall-misconfiguration/cloudfront-use-waf.tf",
            2,
            ["sec_firewall_misconfig", "sec_firewall_misconfig"],
            [1, 14],
        )
        self.__help_test(
            "tests/security/terraform/files/firewall-misconfiguration/config-master-authorized-networks.tf",
            1,
            ["sec_firewall_misconfig"],
            [1],
        )
        self.__help_test(
            "tests/security/terraform/files/firewall-misconfiguration/google-compute-inbound-rule-traffic.tf",
            1,
            ["sec_firewall_misconfig"],
            [1],
        )
        self.__help_test(
            "tests/security/terraform/files/firewall-misconfiguration/google-compute-no-ip-forward.tf",
            1,
            ["sec_firewall_misconfig"],
            [2],
        )
        self.__help_test(
            "tests/security/terraform/files/firewall-misconfiguration/google-compute-outbound-rule-traffic.tf",
            1,
            ["sec_firewall_misconfig"],
            [1],
        )
        self.__help_test(
            "tests/security/terraform/files/firewall-misconfiguration/openstack-compute-no-public-access.tf",
            3,
            [
                "sec_firewall_misconfig",
                "sec_firewall_misconfig",
                "sec_firewall_misconfig",
            ],
            [1, 1, 10],
        )

    def test_terraform_missing_threats_detection_and_alerts(self) -> None:
        self.__help_test(
            "tests/security/terraform/files/missing-threats-detection-and-alerts/azure-database-disabled-alerts.tf",
            1,
            ["sec_threats_detection_alerts"],
            [2],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-threats-detection-and-alerts/azure-database-email-admin.tf",
            2,
            ["sec_threats_detection_alerts", "sec_threats_detection_alerts"],
            [1, 7],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-threats-detection-and-alerts/azure-database-email-for-alerts.tf",
            1,
            ["sec_threats_detection_alerts"],
            [1],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-threats-detection-and-alerts/azure-security-center-alert-notifications.tf",
            2,
            ["sec_threats_detection_alerts", "sec_threats_detection_alerts"],
            [5, 6],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-threats-detection-and-alerts/azure-security-require-contact-phone.tf",
            2,
            ["sec_threats_detection_alerts", "sec_threats_detection_alerts"],
            [1, 10],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-threats-detection-and-alerts/github-repo-vulnerability-alerts.tf",
            2,
            ["sec_threats_detection_alerts", "sec_threats_detection_alerts"],
            [1, 16],
        )
        self.__help_test(
            "tests/security/terraform/files/missing-threats-detection-and-alerts/aws-ecr-enable-image-scans.tf",
            2,
            ["sec_threats_detection_alerts", "sec_threats_detection_alerts"],
            [1, 19],
        )

    def test_terraform_weak_password_key_policy(self) -> None:
        self.__help_test(
            "tests/security/terraform/files/weak-password-key-policy/aws-iam-no-password-reuse.tf",
            2,
            ["sec_weak_password_key_policy", "sec_weak_password_key_policy"],
            [1, 11],
        )
        self.__help_test(
            "tests/security/terraform/files/weak-password-key-policy/aws-iam-require-lowercase-in-passwords.tf",
            2,
            ["sec_weak_password_key_policy", "sec_weak_password_key_policy"],
            [1, 11],
        )
        self.__help_test(
            "tests/security/terraform/files/weak-password-key-policy/aws-iam-require-numbers-in-passwords.tf",
            2,
            ["sec_weak_password_key_policy", "sec_weak_password_key_policy"],
            [1, 11],
        )
        self.__help_test(
            "tests/security/terraform/files/weak-password-key-policy/aws-iam-require-symbols-in-passwords.tf",
            2,
            ["sec_weak_password_key_policy", "sec_weak_password_key_policy"],
            [1, 11],
        )
        self.__help_test(
            "tests/security/terraform/files/weak-password-key-policy/aws-iam-require-uppercase-in-passwords.tf",
            2,
            ["sec_weak_password_key_policy", "sec_weak_password_key_policy"],
            [1, 11],
        )
        self.__help_test(
            "tests/security/terraform/files/weak-password-key-policy/aws-iam-set-max-password-age.tf",
            2,
            ["sec_weak_password_key_policy", "sec_weak_password_key_policy"],
            [1, 11],
        )
        self.__help_test(
            "tests/security/terraform/files/weak-password-key-policy/aws-iam-set-minimum-password-length.tf",
            2,
            ["sec_weak_password_key_policy", "sec_weak_password_key_policy"],
            [1, 11],
        )
        self.__help_test(
            "tests/security/terraform/files/weak-password-key-policy/azure-keyvault-ensure-secret-expiry.tf",
            2,
            ["sec_weak_password_key_policy", "sec_weak_password_key_policy"],
            [1, 11],
        )
        self.__help_test(
            "tests/security/terraform/files/weak-password-key-policy/azure-keyvault-no-purge.tf",
            2,
            ["sec_weak_password_key_policy", "sec_weak_password_key_policy"],
            [1, 11],
        )
        self.__help_test(
            "tests/security/terraform/files/weak-password-key-policy/azure-keyvault-ensure-key-expiration-date.tf",
            2,
            ["sec_weak_password_key_policy", "sec_weak_password_key_policy"],
            [1, 5],
        )

    def test_terraform_integrity_policy(self) -> None:
        self.__help_test(
            "tests/security/terraform/files/integrity-policy/aws-ecr-immutable-repo.tf",
            2,
            ["sec_integrity_policy", "sec_integrity_policy"],
            [1, 13],
        )
        self.__help_test(
            "tests/security/terraform/files/integrity-policy/google-compute-enable-integrity-monitoring.tf",
            1,
            ["sec_integrity_policy"],
            [3],
        )
        self.__help_test(
            "tests/security/terraform/files/integrity-policy/google-compute-enable-virtual-tpm.tf",
            1,
            ["sec_integrity_policy"],
            [3],
        )

    def test_terraform_sensitive_action_by_iam(self) -> None:
        self.__help_test(
            "tests/security/terraform/files/sensitive-action-by-iam/aws-iam-no-policy-wildcards.tf",
            3,
            [
                "sec_sensitive_iam_action",
                "sec_sensitive_iam_action",
                "sec_sensitive_iam_action",
            ],
            [7, 8, 20],
        )

    def test_terraform_key_management(self) -> None:
        self.__help_test(
            "tests/security/terraform/files/key-management/aws-cloudtrail-encryption-use-cmk.tf",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 8],
        )
        self.__help_test(
            "tests/security/terraform/files/key-management/aws-cloudwatch-log-group-customer-key.tf",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 6],
        )
        self.__help_test(
            "tests/security/terraform/files/key-management/aws-documentdb-use-cmk.tf",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 7],
        )
        self.__help_test(
            "tests/security/terraform/files/key-management/aws-dynamodb-table-use-cmk.tf",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 10],
        )
        self.__help_test(
            "tests/security/terraform/files/key-management/aws-ebs-use-cmk.tf",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 7],
        )
        self.__help_test(
            "tests/security/terraform/files/key-management/aws-ecr-use-cmk.tf",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 18],
        )
        self.__help_test(
            "tests/security/terraform/files/key-management/aws-kinesis-stream-use-cmk.tf",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 7],
        )
        self.__help_test(
            "tests/security/terraform/files/key-management/aws-kms-auto-rotate-keys.tf",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 5],
        )
        self.__help_test(
            "tests/security/terraform/files/key-management/aws-neptune-use-cmk.tf",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 9],
        )
        self.__help_test(
            "tests/security/terraform/files/key-management/aws-sns-topic-encryption-use-cmk.tf",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 5],
        )
        self.__help_test(
            "tests/security/terraform/files/key-management/aws-sqs-queue-encryption-use-cmk.tf",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 5],
        )
        self.__help_test(
            "tests/security/terraform/files/key-management/aws-ssm-secret-use-cmk.tf",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 7],
        )
        self.__help_test(
            "tests/security/terraform/files/key-management/azure-storage-account-use-cmk.tf",
            1,
            ["sec_key_management"],
            [1],
        )
        self.__help_test(
            "tests/security/terraform/files/key-management/google-compute-disk-encryption-use-cmk.tf",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 6],
        )
        self.__help_test(
            "tests/security/terraform/files/key-management/google-compute-no-project-wide-ssh-keys.tf",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 12],
        )
        self.__help_test(
            "tests/security/terraform/files/key-management/google-compute-vm-disk-encryption-use-cmk.tf",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 12],
        )
        self.__help_test(
            "tests/security/terraform/files/key-management/google-kms-rotate-kms-keys.tf",
            3,
            ["sec_key_management", "sec_key_management", "sec_key_management"],
            [1, 9, 15],
        )
        self.__help_test(
            "tests/security/terraform/files/key-management/rds-cluster-use-cmk.tf",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 7],
        )
        self.__help_test(
            "tests/security/terraform/files/key-management/rds-instance-use-cmk.tf",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 8],
        )
        self.__help_test(
            "tests/security/terraform/files/key-management/rds-performance-insights-use-cmk.tf",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 9],
        )
        self.__help_test(
            "tests/security/terraform/files/key-management/redshift-cluster-use-cmk.tf",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 7],
        )
        self.__help_test(
            "tests/security/terraform/files/key-management/s3-encryption-customer-key.tf",
            2,
            ["sec_key_management", "sec_key_management"],
            [9, 47],
        )
        self.__help_test(
            "tests/security/terraform/files/key-management/digitalocean-compute-use-ssh-keys.tf",
            1,
            ["sec_key_management"],
            [1],
        )
        self.__help_test(
            "tests/security/terraform/files/key-management/google-storage-bucket-encryption-customer-key.tf",
            2,
            ["sec_key_management", "sec_key_management"],
            [1, 8],
        )

    def test_terraform_network_security_rules(self) -> None:
        self.__help_test(
            "tests/security/terraform/files/network-security-rules/aws-vpc-ec2-use-tcp.tf",
            1,
            ["sec_network_security_rules"],
            [2],
        )
        self.__help_test(
            "tests/security/terraform/files/network-security-rules/azure-container-configured-network-policy.tf",
            2,
            ["sec_network_security_rules", "sec_network_security_rules"],
            [1, 15],
        )
        self.__help_test(
            "tests/security/terraform/files/network-security-rules/azure-network-disable-rdp-from-internet.tf",
            2,
            ["sec_network_security_rules", "sec_network_security_rules"],
            [8, 32],
        )
        self.__help_test(
            "tests/security/terraform/files/network-security-rules/azure-network-ssh-blocked-from-internet.tf",
            2,
            ["sec_network_security_rules", "sec_network_security_rules"],
            [8, 32],
        )
        self.__help_test(
            "tests/security/terraform/files/network-security-rules/azure-storage-default-action-deny.tf",
            3,
            [
                "sec_network_security_rules",
                "sec_network_security_rules",
                "sec_network_security_rules",
            ],
            [1, 8, 21],
        )
        self.__help_test(
            "tests/security/terraform/files/network-security-rules/azure-synapse-virtual-network-enabled.tf",
            2,
            ["sec_network_security_rules", "sec_network_security_rules"],
            [1, 5],
        )
        self.__help_test(
            "tests/security/terraform/files/network-security-rules/google-compute-no-serial-port.tf",
            1,
            ["sec_network_security_rules"],
            [4],
        )
        self.__help_test(
            "tests/security/terraform/files/network-security-rules/google-gke-enable-ip-aliasing.tf",
            1,
            ["sec_network_security_rules"],
            [1],
        )
        self.__help_test(
            "tests/security/terraform/files/network-security-rules/google-gke-enable-network-policy.tf",
            2,
            ["sec_network_security_rules", "sec_network_security_rules"],
            [1, 19],
        )
        self.__help_test(
            "tests/security/terraform/files/network-security-rules/google-iam-no-default-network.tf",
            2,
            ["sec_network_security_rules", "sec_network_security_rules"],
            [1, 5],
        )

    def test_terraform_permission_of_iam_policies(self) -> None:
        self.__help_test(
            "tests/security/terraform/files/permission-of-iam-policies/default-service-account-not-used-at-folder-level.tf",
            2,
            ["sec_permission_iam_policies", "sec_permission_iam_policies"],
            [4, 10],
        )
        self.__help_test(
            "tests/security/terraform/files/permission-of-iam-policies/default-service-account-not-used-at-organization-level.tf",
            2,
            ["sec_permission_iam_policies", "sec_permission_iam_policies"],
            [4, 10],
        )
        self.__help_test(
            "tests/security/terraform/files/permission-of-iam-policies/default-service-account-not-used-at-project-level.tf",
            2,
            ["sec_permission_iam_policies", "sec_permission_iam_policies"],
            [4, 10],
        )
        self.__help_test(
            "tests/security/terraform/files/permission-of-iam-policies/google-iam-no-folder-level-service-account-impersonation.tf",
            1,
            ["sec_permission_iam_policies"],
            [3],
        )
        self.__help_test(
            "tests/security/terraform/files/permission-of-iam-policies/google-iam-no-organization-level-service-account-impersonation.tf",
            1,
            ["sec_permission_iam_policies"],
            [3],
        )
        self.__help_test(
            "tests/security/terraform/files/permission-of-iam-policies/google-iam-no-project-level-service-account-impersonation.tf",
            1,
            ["sec_permission_iam_policies"],
            [3],
        )
        self.__help_test(
            "tests/security/terraform/files/permission-of-iam-policies/google-iam-no-user-granted-permissions.tf",
            2,
            ["sec_permission_iam_policies", "sec_permission_iam_policies"],
            [2, 6],
        )
        self.__help_test(
            "tests/security/terraform/files/permission-of-iam-policies/iam-policies-attached-only-to-groups-or-roles.tf",
            1,
            ["sec_permission_iam_policies"],
            [7],
        )

    def test_terraform_logging(self) -> None:
        self.__help_test(
            "tests/security/terraform/files/logging/aws-api-gateway-enable-access-logging.tf",
            4,
            ["sec_logging", "sec_logging", "sec_logging", "sec_logging"],
            [1, 4, 10, 17],
        )
        self.__help_test(
            "tests/security/terraform/files/logging/aws-api-gateway-enable-tracing.tf",
            2,
            ["sec_logging", "sec_logging"],
            [1, 9],
        )
        self.__help_test(
            "tests/security/terraform/files/logging/aws-cloudfront-enable-logging.tf",
            2,
            ["sec_logging", "sec_logging"],
            [1, 13],
        )
        self.__help_test(
            "tests/security/terraform/files/logging/aws-cloudtrail-enable-log-validation.tf",
            2,
            ["sec_logging", "sec_logging"],
            [1, 7],
        )
        self.__help_test(
            "tests/security/terraform/files/logging/aws-cloudtrail-ensure-cloudwatch-integration.tf",
            2,
            ["sec_logging", "sec_logging"],
            [1, 7],
        )
        self.__help_test(
            "tests/security/terraform/files/logging/aws-documentdb-enable-log-export.tf",
            2,
            ["sec_logging", "sec_logging"],
            [1, 7],
        )
        self.__help_test(
            "tests/security/terraform/files/logging/aws-eks-enable-control-plane-logging.tf",
            2,
            ["sec_logging", "sec_logging"],
            [1, 15],
        )
        self.__help_test(
            "tests/security/terraform/files/logging/aws-elastic-search-enable-domain-logging.tf",
            3,
            ["sec_logging", "sec_logging", "sec_logging"],
            [1, 17, 36],
        )
        self.__help_test(
            "tests/security/terraform/files/logging/aws-lambda-enable-tracing.tf",
            2,
            ["sec_logging", "sec_logging"],
            [1, 6],
        )
        self.__help_test(
            "tests/security/terraform/files/logging/aws-mq-enable-audit-logging.tf",
            2,
            ["sec_logging", "sec_logging"],
            [1, 10],
        )
        self.__help_test(
            "tests/security/terraform/files/logging/aws-mq-enable-general-logging.tf",
            2,
            ["sec_logging", "sec_logging"],
            [1, 10],
        )
        self.__help_test(
            "tests/security/terraform/files/logging/aws-msk-enable-logging.tf",
            5,
            ["sec_logging", "sec_logging", "sec_logging", "sec_logging", "sec_logging"],
            [1, 14, 48, 51, 54],
        )
        self.__help_test(
            "tests/security/terraform/files/logging/aws-neptune-enable-log-export.tf",
            2,
            ["sec_logging", "sec_logging"],
            [1, 7],
        )
        self.__help_test(
            "tests/security/terraform/files/logging/aws-rds-enable-performance-insights.tf",
            2,
            ["sec_logging", "sec_logging"],
            [1, 7],
        )
        self.__help_test(
            "tests/security/terraform/files/logging/aws-s3-enable-bucket-logging.tf",
            1,
            ["sec_logging"],
            [1],
        )
        self.__help_test(
            "tests/security/terraform/files/logging/azure-container-aks-logging-configured.tf",
            2,
            ["sec_logging", "sec_logging"],
            [1, 13],
        )
        self.__help_test(
            "tests/security/terraform/files/logging/azure-monitor-activity-log-retention-set.tf",
            2,
            ["sec_logging", "sec_logging"],
            [1, 8],
        )
        self.__help_test(
            "tests/security/terraform/files/logging/azure-monitor-capture-all-activities.tf",
            2,
            ["sec_logging", "sec_logging"],
            [1, 8],
        )
        self.__help_test(
            "tests/security/terraform/files/logging/azure-mssql-database-enable-audit.tf",
            1,
            ["sec_logging"],
            [1],
        )
        self.__help_test(
            "tests/security/terraform/files/logging/azure-mssql-server-and-database-retention-period-set.tf",
            3,
            ["sec_logging", "sec_logging", "sec_logging"],
            [3, 13, 18],
        )
        self.__help_test(
            "tests/security/terraform/files/logging/azure-mssql-server-enable-audit.tf",
            1,
            ["sec_logging"],
            [1],
        )
        self.__help_test(
            "tests/security/terraform/files/logging/azure-network-retention-policy-set.tf",
            2,
            ["sec_logging", "sec_logging"],
            [1, 7],
        )
        self.__help_test(
            "tests/security/terraform/files/logging/azure-postgres-configuration-enabled-logs.tf",
            3,
            ["sec_logging", "sec_logging", "sec_logging"],
            [5, 12, 19],
        )
        self.__help_test(
            "tests/security/terraform/files/logging/azure-storage-queue-services-logging-enabled.tf",
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
        self.__help_test(
            "tests/security/terraform/files/logging/ensure-cloudwatch-log-group-specifies-retention-days.tf",
            2,
            ["sec_logging", "sec_logging"],
            [1, 6],
        )
        self.__help_test(
            "tests/security/terraform/files/logging/google-compute-enable-vpc-flow-logs.tf",
            1,
            ["sec_logging"],
            [1],
        )
        self.__help_test(
            "tests/security/terraform/files/logging/google-gke-enable-stackdriver-logging.tf",
            1,
            ["sec_logging"],
            [2],
        )
        self.__help_test(
            "tests/security/terraform/files/logging/google-gke-enable-stackdriver-monitoring.tf",
            1,
            ["sec_logging"],
            [2],
        )
        self.__help_test(
            "tests/security/terraform/files/logging/google-sql-database-log-flags.tf",
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
        self.__help_test(
            "tests/security/terraform/files/logging/storage-logging-enabled-for-blob-service-for-read-requests.tf",
            4,
            ["sec_logging", "sec_logging", "sec_logging", "sec_logging"],
            [1, 8, 49, 79],
        )
        self.__help_test(
            "tests/security/terraform/files/logging/aws-ecs-enable-container-insight.tf",
            3,
            ["sec_logging", "sec_logging", "sec_logging"],
            [1, 7, 11],
        )
        self.__help_test(
            "tests/security/terraform/files/logging/aws-vpc-flow-logs-enabled.tf",
            1,
            ["sec_logging"],
            [11],
        )

    def test_terraform_attached_resource(self) -> None:
        self.__help_test(
            "tests/security/terraform/files/attached-resource/aws_route53_attached_resource.tf",
            2,
            ["sec_attached_resource", "sec_attached_resource"],
            [12, 16],
        )

    def test_terraform_versioning(self) -> None:
        self.__help_test(
            "tests/security/terraform/files/versioning/aws-s3-enable-versioning.tf",
            2,
            ["sec_versioning", "sec_versioning"],
            [1, 8],
        )
        self.__help_test(
            "tests/security/terraform/files/versioning/digitalocean-spaces-versioning-enabled.tf",
            2,
            ["sec_versioning", "sec_versioning"],
            [1, 7],
        )

    def test_terraform_naming(self) -> None:
        self.__help_test(
            "tests/security/terraform/files/naming/aws-ec2-description-to-security-group-rule.tf",
            2,
            ["sec_naming", "sec_naming"],
            [1, 14],
        )
        self.__help_test(
            "tests/security/terraform/files/naming/aws-ec2-description-to-security-group.tf",
            2,
            ["sec_naming", "sec_naming"],
            [1, 5],
        )
        self.__help_test(
            "tests/security/terraform/files/naming/aws-elasticache-description-for-security-group.tf",
            2,
            ["sec_naming", "sec_naming"],
            [1, 7],
        )
        self.__help_test(
            "tests/security/terraform/files/naming/naming-rules-storage-accounts.tf",
            2,
            ["sec_naming", "sec_naming"],
            [2, 21],
        )
        self.__help_test(
            "tests/security/terraform/files/naming/openstack-networking-describe-security-group.tf",
            2,
            ["sec_naming", "sec_naming"],
            [1, 5],
        )
        self.__help_test(
            "tests/security/terraform/files/naming/google-gke-use-cluster-labels.tf",
            2,
            ["sec_naming", "sec_naming"],
            [1, 19],
        )

    def test_terraform_replication(self) -> None:
        self.__help_test(
            "tests/security/terraform/files/replication/s3-bucket-cross-region-replication.tf",
            2,
            ["sec_replication", "sec_replication"],
            [9, 16],
        )
