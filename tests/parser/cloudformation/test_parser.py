from glitch.parsers.cloudformation import CloudFormationParser
from glitch.repr.inter import *
from tests.parser.test_parser import TestParser


class TestCloudFormationParser(TestParser):
    def __parse(self, path: str) -> UnitBlock:
        p = CloudFormationParser()
        ir = p.parse_file(path, UnitBlockType.script)
        assert ir is not None
        assert isinstance(ir, UnitBlock)
        return ir

    def test_cf_parser_s3_bucket(self) -> None:
        ir = self.__parse("tests/parser/cloudformation/files/s3_bucket.yaml")
        assert len(ir.atomic_units) == 1

        au = ir.atomic_units[0]
        assert isinstance(au, AtomicUnit)
        self._check_value(au.name, String, "MyBucket", 3, 3, 3, 11)
        assert au.type == "AWS::S3::Bucket"
        assert len(au.attributes) == 2

        assert au.attributes[0].name == "BucketName"
        assert au.attributes[0].line == 6
        assert au.attributes[0].column == 7
        assert au.attributes[0].end_line == 6
        assert au.attributes[0].end_column == 33
        self._check_value(
            au.attributes[0].value, String, "my-test-bucket", 6, 19, 6, 33
        )

        assert au.attributes[1].name == "AccessControl"
        assert au.attributes[1].line == 7
        assert au.attributes[1].column == 7
        assert au.attributes[1].end_line == 7
        assert au.attributes[1].end_column == 29
        self._check_value(au.attributes[1].value, String, "Private", 7, 22, 7, 29)

    def test_cf_parser_no_properties(self) -> None:
        ir = self.__parse("tests/parser/cloudformation/files/no_properties.yaml")
        assert len(ir.atomic_units) == 1

        au = ir.atomic_units[0]
        assert isinstance(au, AtomicUnit)
        self._check_value(au.name, String, "MyRole", 3, 3, 3, 9)
        assert au.type == "AWS::IAM::Role"
        assert len(au.attributes) == 0

    def test_cf_parser_ec2_instance(self) -> None:
        ir = self.__parse("tests/parser/cloudformation/files/ec2_instance.yaml")
        assert len(ir.atomic_units) == 1

        au = ir.atomic_units[0]
        assert isinstance(au, AtomicUnit)
        self._check_value(au.name, String, "MyInstance", 3, 3, 3, 13)
        assert au.type == "AWS::EC2::Instance"
        assert len(au.attributes) == 2

        assert au.attributes[0].name == "InstanceType"
        self._check_value(
            au.attributes[0].value, String, "t2.micro", 6, 21, 6, 29
        )

        assert au.attributes[1].name == "AvailabilityZone"
        self._check_value(
            au.attributes[1].value, String, "us-east-1a", 7, 25, 7, 35
        )

    def test_cf_parser_iam_role(self) -> None:
        ir = self.__parse("tests/parser/cloudformation/files/iam_role.yaml")
        assert len(ir.atomic_units) == 1

        au = ir.atomic_units[0]
        assert isinstance(au, AtomicUnit)
        self._check_value(au.name, String, "MyRole", 3, 3, 3, 9)
        assert au.type == "AWS::IAM::Role"
        assert len(au.attributes) == 1

        assert au.attributes[0].name == "AssumeRolePolicyDocument"
        assert isinstance(au.attributes[0].value, Hash)
        assert au.attributes[0].value.line == 7
        assert au.attributes[0].value.column == 9
        assert au.attributes[0].value.end_line == 12
        assert au.attributes[0].value.end_column == 35

    def test_cf_parser_parameters(self) -> None:
        ir = self.__parse("tests/parser/cloudformation/files/parameters.yaml")
        assert len(ir.atomic_units) == 1
        assert len(ir.variables) == 2

        v1 = ir.variables[0]
        assert v1.name == "BucketNameParam"
        assert v1.line == 3
        assert v1.column == 3
        assert v1.end_line == 6
        assert v1.end_column == 3
        self._check_value(v1.value, String, "my-bucket", 5, 14, 5, 23)

        v2 = ir.variables[1]
        assert v2.name == "NoDefaultParam"
        assert isinstance(v2.value, Null)
        assert v2.value.line == 6
        assert v2.value.column == 3
        assert v2.value.end_line == 6
        assert v2.value.end_column == 17

    def test_cf_parser_ref(self) -> None:
        ir = self.__parse("tests/parser/cloudformation/files/ref_intrinsic.yaml")
        assert len(ir.atomic_units) == 1
        au = ir.atomic_units[0]
        assert len(au.attributes) == 2

        assert au.attributes[0].name == "BucketName"
        self._check_value(
            au.attributes[0].value, VariableReference, "BucketNameParam", 6, 19, 6, 39
        )

        assert au.attributes[1].name == "AccessControl"
        self._check_value(
            au.attributes[1].value, VariableReference, "BucketNameParam", 8, 9, 9, 1
        )

    def test_cf_parser_getatt(self) -> None:
        ir = self.__parse("tests/parser/cloudformation/files/getatt_intrinsic.yaml")
        assert len(ir.atomic_units) == 3

        au1 = ir.atomic_units[0]
        assert au1.name.value == "MyBucket"
        assert len(au1.attributes) == 1
        assert au1.attributes[0].name == "BucketName"
        assert isinstance(au1.attributes[0].value, Access)
        self._check_value(
            au1.attributes[0].value.left, VariableReference, "MyRole", 6, 19, 6, 37
        )
        self._check_value(
            au1.attributes[0].value.right, String, "Arn", 6, 19, 6, 37
        )

        au2 = ir.atomic_units[1]
        assert au2.name.value == "MyInstance"
        assert len(au2.attributes) == 1
        assert au2.attributes[0].name == "AvailabilityZone"
        assert isinstance(au2.attributes[0].value, Access)
        self._check_value(
            au2.attributes[0].value.left, VariableReference, "MyBucket", 10, 25, 10, 48
        )
        self._check_value(
            au2.attributes[0].value.right, String, "Arn", 10, 25, 10, 48
        )

        au3 = ir.atomic_units[2]
        assert au3.name.value == "MyRole"
        assert len(au3.attributes) == 1
        assert au3.attributes[0].name == "RoleName"
        assert isinstance(au3.attributes[0].value, Access)
        self._check_value(
            au3.attributes[0].value.left, VariableReference, "MyBucket", 16, 11, 18, 1
        )
        self._check_value(
            au3.attributes[0].value.right, String, "Arn", 16, 11, 18, 1
        )

    def test_cf_parser_depends_on(self) -> None:
        ir = self.__parse("tests/parser/cloudformation/files/depends_on.yaml")
        assert len(ir.atomic_units) == 3
        assert len(ir.dependencies) == 3

        assert ir.dependencies[0].names == ["MyRole"]
        assert ir.dependencies[0].line == 5

        assert ir.dependencies[1].names == ["MyBucket"]
        assert ir.dependencies[1].line == 11

        assert ir.dependencies[2].names == ["MyRole"]
        assert ir.dependencies[2].line == 12

    def test_cf_parser_mappings_conditions(self) -> None:
        ir = self.__parse(
            "tests/parser/cloudformation/files/mappings_conditions.yaml"
        )
        assert len(ir.atomic_units) == 1
        assert len(ir.variables) == 2

        assert ir.variables[0].name == "RegionMap"
        assert isinstance(ir.variables[0].value, Hash)

        assert ir.variables[1].name == "IsProd"
        assert isinstance(ir.variables[1].value, Array)

    def test_cf_parser_comments(self) -> None:
        ir = self.__parse("tests/parser/cloudformation/files/comments.yaml")
        assert len(ir.comments) == 3

        comments_sorted = sorted(ir.comments, key=lambda c: c.line)
        assert comments_sorted[0].content == "# This is a comment"
        assert comments_sorted[0].line == 1

        assert comments_sorted[1].content == "# Another comment"
        assert comments_sorted[1].line == 3

        assert comments_sorted[2].content == "# Inline comment"
        assert comments_sorted[2].line == 7
