from typing import List
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, CodeElement, KeyValue


class TerraformHttpWithoutTls(TerraformSmellChecker):
    def _check_attribute(
        self,
        attribute: Attribute | KeyValue,
        atomic_unit: AtomicUnit,
        parent_name: str,
        file: str,
    ) -> List[Error]:
        for config in SecurityVisitor.HTTPS_CONFIGS:
            if (
                attribute.name == config["attribute"]
                and atomic_unit.type in config["au_type"]
                and parent_name in config["parents"]
                and not attribute.has_variable
                and isinstance(attribute.value, str)
                and attribute.value.lower() not in config["values"]
            ):
                return [Error("sec_https", attribute, file, repr(attribute))]

        return []

    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []
        if isinstance(element, AtomicUnit):
            if element.type == "data.http":
                url = self.check_required_attribute(element.attributes, [""], "url")
                if (
                    isinstance(url, KeyValue)
                    and isinstance(url.value, str)
                    and "${" in url.value
                ):
                    vars = url.value.split("${")
                    r = url.value.split("${")[1].split("}")[0]
                    for var in vars:
                        if "data" in var or "resource" in var:
                            r = var.split("}")[0]
                            break
                    type = r.split(".")[0]
                    if type in ["data", "resource"]:
                        resource_type = r.split(".")[1]
                        resource_name = r.split(".")[2]
                    else:
                        type = "resource"
                        resource_type = r.split(".")[0]
                        resource_name = r.split(".")[1]
                    if self.get_au(file, resource_name, type + "." + resource_type):
                        errors.append(Error("sec_https", url, file, repr(url)))

            for config in SecurityVisitor.HTTPS_CONFIGS:
                if (
                    config["required"] == "yes"
                    and element.type in config["au_type"]
                    and not self.check_required_attribute(
                        element.attributes, config["parents"], config["attribute"]
                    )
                ):
                    errors.append(
                        Error(
                            "sec_https",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required attribute with name '{config['msg']}'.",
                        )
                    )

            errors += self._check_attributes(element, file)

        return errors
