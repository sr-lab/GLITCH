import unittest

from glitch.analysis.security import SecurityVisitor
from glitch.parsers.cmof import TerraformParser
from glitch.tech import Tech

class TestSecurity(unittest.TestCase):
    def __help_test(self, path, n_errors, codes, lines):
        parser = TerraformParser()
        inter = parser.parse(path, "script", False)
        analysis = SecurityVisitor(Tech.terraform)
        analysis.config("configs/default.ini")
        errors = list(filter(lambda e: e.code.startswith('sec_'), set(analysis.check(inter))))
        errors = sorted(errors, key=lambda e: (e.path, e.line, e.code))
        self.assertEqual(len(errors), n_errors)
        for i in range(n_errors):
            self.assertEqual(errors[i].code, codes[i])
            self.assertEqual(errors[i].line, lines[i])  

    # testing previous implemented code smells
    def test_terraform_http(self):
        self.__help_test(
            "tests/security/terraform/files/http.tf",
            1, ["sec_https"], [2]
        )

    def test_terraform_susp_comment(self):
        self.__help_test(
            "tests/security/terraform/files/susp.tf",
            1, ["sec_susp_comm"], [8]
        )

    def test_terraform_def_admin(self):
        self.__help_test(
            "tests/security/terraform/files/admin.tf",
            3, ["sec_def_admin", "sec_hard_secr", "sec_hard_user"], [2, 2, 2]
        )

    def test_terraform_empt_pass(self):
        self.__help_test(
            "tests/security/terraform/files/empty.tf",
            3, ["sec_empty_pass", "sec_hard_pass", "sec_hard_secr"], [5, 5, 5]
        )

    def test_terraform_weak_crypt(self):
        self.__help_test(
            "tests/security/terraform/files/weak_crypt.tf",
            1, ["sec_weak_crypt"], [4]
        )

    def test_terraform_hard_secr(self):
        self.__help_test(
            "tests/security/terraform/files/hard_secr.tf",
            2, 
            ["sec_hard_pass", "sec_hard_secr"]
            , [5, 5]
        )

    def test_terraform_invalid_bind(self):
        self.__help_test(
            "tests/security/terraform/files/inv_bind.tf",
            1, ["sec_invalid_bind"], [19]
        )

    # testing new implemented code smells, or previous ones with new rules for Terraform

    def test_terraform_insecure_access_control(self):
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/access-to-bigquery-dataset.tf",
            1, ["sec_access_control"], [3]
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/aks-ip-ranges-enabled.tf",
            1, ["sec_access_control"], [1]
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/associated-access-block-to-s3-bucket.tf",
            1, ["sec_access_control"], [1]
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/aws-database-instance-publicly-accessible.tf",
            2, ["sec_access_control", "sec_access_control"], [2, 16]
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/aws-sqs-no-wildcards-in-policy.tf",
            1, ["sec_access_control"], [4]
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/azure-authorization-wildcard-action.tf",
            1, ["sec_access_control"], [7]
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/azure-container-use-rbac-permissions.tf",
            1, ["sec_access_control"], [2]
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/azure-database-not-publicly-accessible.tf",
            2, ["sec_access_control", "sec_access_control"], [1, 6]
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/bucket-public-read-acl.tf",
            3, ["sec_access_control", "sec_access_control", "sec_access_control"], [1, 8, 25]
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/cidr-range-public-access-eks-cluster.tf",
            1, ["sec_access_control"], [1]
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/cross-db-ownership-chaining.tf",
            3, ["sec_access_control", "sec_access_control", "sec_access_control"], [1, 50, 97]
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/data-factory-public-access.tf",
            2, ["sec_access_control", "sec_access_control"], [1, 5]
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/google-compute-no-default-service-account.tf",
            2, ["sec_access_control", "sec_access_control"], [1, 19]
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/google-gke-use-rbac-permissions.tf",
            1, ["sec_access_control"], [14]
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/google-storage-enable-ubla.tf",
            2, ["sec_access_control", "sec_access_control"], [1, 5]
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/google-storage-no-public-access.tf",
            3, ["sec_access_control", "sec_access_control", "sec_access_control"], [4, 10, 22]
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/mq-broker-publicly-exposed.tf",
            1, ["sec_access_control"], [2]
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/prevent-client-disable-encryption.tf",
            1, ["sec_access_control"], [13]
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/private-cluster-nodes.tf",
            2, ["sec_access_control", "sec_access_control"], [1, 16]
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/public-access-eks-cluster.tf",
            1, ["sec_access_control"], [10]
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/public-access-policy.tf",
            1, ["sec_access_control"], [4]
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/public-github-repo.tf",
            3, ["sec_access_control", "sec_access_control", "sec_access_control"], [1, 6, 18]
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/s3-access-through-acl.tf",
            1, ["sec_access_control"], [7]
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/s3-block-public-acl.tf",
            2, ["sec_access_control", "sec_access_control"], [1, 10]
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/s3-block-public-policy.tf",
            2, ["sec_access_control", "sec_access_control"], [1, 11]
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/s3-ignore-public-acl.tf",
            2, ["sec_access_control", "sec_access_control"], [1, 13]
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/s3-restrict-public-bucket.tf",
            2, ["sec_access_control", "sec_access_control"], [1, 12]
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/specify-source-lambda-permission.tf",
            1, ["sec_access_control"], [1]
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/storage-containers-public-access.tf",
            1, ["sec_access_control"], [26]
        )
        self.__help_test(
            "tests/security/terraform/files/insecure-access-control/unauthorized-access-api-gateway-methods.tf",
            2, ["sec_access_control", "sec_access_control"], [37, 44]
        )

if __name__ == '__main__':
    unittest.main()