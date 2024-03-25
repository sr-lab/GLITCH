import re
from typing import List
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, CodeElement, KeyValue


class TerraformReplication(TerraformSmellChecker):
    def _check_attribute(
        self,
        attribute: Attribute | KeyValue,
        atomic_unit: AtomicUnit,
        parent_name: str,
        file: str,
    ) -> List[Error]:
        for config in SecurityVisitor.REPLICATION:
            if (
                attribute.name == config["attribute"]
                and atomic_unit.type in config["au_type"]
                and parent_name in config["parents"]
                and config["values"] != [""]
                and not attribute.has_variable
                and isinstance(attribute.value, str)
                and attribute.value.lower() not in config["values"]
            ):
                return [Error("sec_replication", attribute, file, repr(attribute))]

        return []

    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []
        if isinstance(element, AtomicUnit):
            if element.type == "resource.aws_s3_bucket":
                expr = "\\${aws_s3_bucket\\." + f"{element.name}\\."
                pattern = re.compile(rf"{expr}")
                if not self.get_associated_au(
                    file,
                    "resource.aws_s3_bucket_replication_configuration",
                    "bucket",
                    pattern,
                    [""],
                ):
                    errors.append(
                        Error(
                            "sec_replication",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required resource 'aws_s3_bucket_replication_configuration' "
                            + f"associated to an 'aws_s3_bucket' resource.",
                        )
                    )

            for config in SecurityVisitor.REPLICATION:
                if (
                    config["required"] == "yes"
                    and element.type in config["au_type"]
                    and not self.check_required_attribute(
                        element.attributes, config["parents"], config["attribute"]
                    )
                ):
                    errors.append(
                        Error(
                            "sec_replication",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required attribute with name '{config['msg']}'.",
                        )
                    )

            errors += self._check_attributes(element, file)

        return errors
